#!/usr/bin/python3
import sys
import os
import getopt
import queue
import time
import concurrent.futures
import socket
import ssl
from netaddr import IPNetwork, IPRange

filename = "addr.txt"
output = ""
timeout = 5
maxthreads = 1000
hostname = "cdnjs.cloudflare.com"
result_ips = []
i = ""

times = 0
n = 0

def usage():
    helps = """ -f, --file        import IP ranges from file (default: addr.txt)
 -i, --ip          IP range to scan, will override -f argument (optional)
 -o, --out         filename to save, 0 results won't write (optional)
 -m, --maxthreads  number of scanner threads (default: 1000)
 -t, --timeout     connection timeout (default: 5)
 -n, --hostname    set a hostname/servername (default: "cdnjs.cloudflare.com")
 -h, --help        get help"""
    print(helps)

def gen_ip(a):
    # TODO
    ipQueue = queue.Queue()
    txt = a
    list1 = txt.split("\n")
    for n in list1:
        list2 = n.split("-")
        list3 = n.split("/")
        if len(list2) == 2:
            tmp = IPRange(list2[0],list2[1])
            for b in tmp:
                ipQueue.put(b)
        elif len(list3) == 2:
            tmp = IPNetwork(n)
            for b in tmp:
                ipQueue.put(str(b))
        elif len(list3) == 1:
            b = str(list3[0])
            ipQueue.put(b)
    #ipQueue.qsize()
    return ipQueue

def tlsprobe(ip, timeout, hostname) :
    c = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    c.verify_mode = ssl.CERT_REQUIRED
    c.check_hostname = True
    c.load_default_certs()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    ssl_sock = c.wrap_socket(s, server_hostname = hostname)
    try:
        ssl_sock.connect((ip, 443))
        return True
    #except socket.timeout:
    #except ssl.SSLCertVerificationError:
    except:
        return False
    finally:
        ssl_sock.close()
        s.close()

def worker(t, h):
    global times, result_ips, ipQueue
    try:
        ip = ipQueue.get(timeout = 5)
    except:
        pass
    else:
        r = tlsprobe(ip, t, h)
        times += 1
        if r == True:
            # TODO
            result_ips.append(ip)
            printx ("Discovered " + ip, 1)
    printx()

def printx(text = "", type = 0):
    # TODO: ETA
    global times, n

    p = str(int((times/n) * 100))
    if type == 1:
        print(text)
    else:
        # TODO
        sys.stdout.write(p + "% \r")
        sys.stdout.flush()

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:i:o:t:m:n:h", ["file=", "ip=", "out=", "timeout=", "maxthreads=", "hostname=", "help"])
    except getopt.GetoptError as err:
        print(err, file=sys.stderr)
        usage()
        sys.exit(1)

    global filename, output, timeout, maxthreads, hostname, ipQueue, n, i

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
                sys.stderr.write("error: argument to -timeout must be more than 0\n")
                sys.exit(1)
        elif o in ("-n", "--hostname"):
            hostname = a
        elif o in ("-m", "--maxthreads"):
            maxthreads = int(a)
            if maxthreads <= 0:
                sys.stderr.write("error: argument to -maxthreads must be at least 1\n")
                sys.exit(1)

    file_obj = open(filename)

    try:
        if i != "":
            txt = i
        else:
            txt = file_obj.read()
        ipQueue = gen_ip(txt)
        print("Scanning " + str(ipQueue.qsize()) + " IPs")
    finally:
        file_obj.close()

    executor = concurrent.futures.ThreadPoolExecutor(maxthreads)
    n = ipQueue.qsize()

    all_task = [executor.submit(worker, timeout, hostname) for i in range(n)]

    printx()

    concurrent.futures.wait(all_task)
    executor.shutdown(wait=True)

    # TODO
    print("Finish. " + "Scanned "+ str(times) +" IPs, " + str(len(result_ips)) +" IPs matched hostname.")

    if len(result_ips) == 0:
        sys.exit(0)
    elif output != "":
        if output == "time":
            name = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))
            output = "result-" + name +".txt"
        f = open(output, "w")
        try:
            for v in result_ips:
                f.writelines(v+"\n")
        finally:
            f.close()
            print("Save to " + os.path.abspath(output), file=sys.stdout)
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('KeyboardInterrupt', file=sys.stderr)
        try:
            sys.exit(1)
        except SystemExit:
            os._exit(1)
