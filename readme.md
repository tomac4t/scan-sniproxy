# Scan sniproxy

Usage：
```bash
$ python scan-sniproxy.py --help
 -f, --file <file>         Import IP ranges from file, addr.txt by default
 -o, --out <file>          Filename to save, result-<datetime>.txt by default
 -m, --maxthreads [number] number of scanner threads, 1000 threads by default
 -t, --timeout [float]     connection timeout, 5 seconds by default
 -n, --hostname            Set a hostname/servername, "cdnjs.cloudflare.com" by default
 -h, --help                Get help for commands
$ python scan-sniproxy.py
Scanning 768 IPs
Discovered 106.14.176.3
Discovered 211.72.35.110
Discovered 211.72.35.119
Finish. Scanned 768 IPs, 3 IPs matched hostname.
```

Example `addr.txt`: 
```
1.0.0.1-1.1.1.1
8.8.4.4
8.8.8.0/24
```

To avoid scanning a lot of CDN IPs, consider using a servername whois website without behind CDN. 

Blog of the origin author: [garnote.top](http://garnote.top)