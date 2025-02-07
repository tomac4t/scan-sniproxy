#!/usr/bin/python3
import sys
import os
import getopt
import queue
import time
import concurrent.futures
import socket
import ssl
import threading
from netaddr import IPNetwork, IPRange

filename = "addr.txt"
output = ""
timeout = 5
maxthreads = 200
hostname = "cdnjs.cloudflare.com"
result_ips = []
i = ""

times = 0
n = 0

times_lock = threading.Lock()
result_lock = threading.Lock()
print_lock = threading.Lock()

def usage():
    helps = """ -f, --file        import IP ranges from file (default: addr.txt)
 -i, --ip          IP range to scan, will override -f argument (optional)
 -o, --out         filename to save, 0 results won't write (optional)
 -m, --maxthreads  number of scanner threads (default: 200)
 -t, --timeout     connection timeout (default: 5)
 -n, --hostname    set a hostname/servername (default: "cdnjs.cloudflare.com")
 -h, --help        get help"""
    print(helps)

def gen_ip(txt):
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        if '-' in line:
            start, end = line.split('-', 1)
            ip_range = IPRange(start.strip(), end.strip())
            for ip in ip_range:
                yield str(ip)
        elif '/' in line:
            network = IPNetwork(line)
            for ip in network:
                yield str(ip)
        else:
            yield line

def calculate_total(txt):
    total = 0
    for line in txt.splitlines():
        line = line.strip()
        if not line:
            continue
        if '-' in line:
            start, end = line.split('-', 1)
            total += IPRange(start.strip(), end.strip()).size
        elif '/' in line:
            network = IPNetwork(line)
            total += network.size
        else:
            total += 1
    return total

def tlsprobe(ip, hostname, timeout):
    c = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    c.verify_mode = ssl.CERT_REQUIRED
    c.check_hostname = True
    c.load_default_certs()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    ssl_sock = c.wrap_socket(s, server_hostname=hostname)
    try:
        ssl_sock.connect((ip, 443))
        return True
    except:
        return False
    finally:
        ssl_sock.close()
        s.close()

def worker(t, h, q, output_file):
    global times
    while True:
        try:
            ip = q.get(timeout=5)
            if ip is None:  # 终止信号
                q.put(None)
                break

            result = tlsprobe(ip, h, t)
            
            with times_lock:
                times += 1
                progress = (times / n) * 100 if n != 0 else 0
                sys.stdout.write(f"\rScanning: {progress:.1f}% ({times}/{n})")
                sys.stdout.flush()

            if result:
                with result_lock:
                    if output_file:
                        output_file.write(ip + '\n')
                        output_file.flush()
                    result_ips.append(ip)
                with print_lock:
                    print(f"\nDiscovered {ip}")

        except queue.Empty:
            break

def main():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 
            "f:i:o:t:m:n:h", 
            ["file=", "ip=", "out=", "timeout=", "maxthreads=", "hostname=", "help"]
        )
    except getopt.GetoptError as err:
        print(err, file=sys.stderr)
        usage()
        sys.exit(1)

    global filename, output, timeout, maxthreads, hostname, n, i

    for o, a in opts:
        if o in ("-f", "--file"):
            filename = a
        elif o in ("-i", "--ip"):
            i = a
        elif o in ("-o", "--out"):
            output = a
        elif o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-t", "--timeout"):
            timeout = float(a)
            if timeout <= 0:
                sys.stderr.write("error: timeout must > 0\n")
                sys.exit(1)
        elif o in ("-n", "--hostname"):
            hostname = a
        elif o in ("-m", "--maxthreads"):
            maxthreads = int(a)
            if maxthreads <= 0:
                sys.stderr.write("error: maxthreads must >= 1\n")
                sys.exit(1)

    try:
        if i:
            txt = i
        else:
            with open(filename) as f:
                txt = f.read()
        
        n = calculate_total(txt)
        print(f"Scanning {n} IPs")
        
        output_file = None
        if output:
            if output == "time":
                output = f"result-{time.strftime('%Y%m%d%H%M%S')}.txt"
            output_file = open(output, "w")

        # 使用有界队列防止内存膨胀
        ip_queue = queue.Queue(maxsize=maxthreads*2)
        
        # 启动生产者线程
        producer = threading.Thread(
            target=lambda: (
                [ip_queue.put(ip) for ip in gen_ip(txt)],
                ip_queue.put(None)  # 结束信号
            )
        )
        producer.start()

        # 启动消费者线程池
        with concurrent.futures.ThreadPoolExecutor(maxthreads) as executor:
            futures = [
                executor.submit(
                    worker,
                    timeout,
                    hostname,
                    ip_queue,
                    output_file
                )
                for _ in range(maxthreads)
            ]
            concurrent.futures.wait(futures)

        producer.join()
        if output_file:
            output_file.close()
            print(f"\nSaved to {os.path.abspath(output)}")

    except KeyboardInterrupt:
        print("\nScan interrupted")
    finally:
        if output_file:
            output_file.close()

    print(f"\nScanned {times} IPs, found {len(result_ips)} matches")

if __name__ == "__main__":
    main()