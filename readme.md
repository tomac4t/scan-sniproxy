# Scan sniproxy

Usage：
```bash
$ python scan-sniproxy.py --help
 -f, --file        import IP ranges from file (default: addr.txt)
 -i, --ip          IP range to scan, will override -f argument (optional)
 -o, --out         filename to save, 0 results won't write (optional)
 -m, --maxthreads  number of scanner threads (default: 1000)
 -t, --timeout     connection timeout (default: 5)
 -n, --hostname    set a hostname/servername (default: "cdnjs.cloudflare.com")
 -h, --help        get help
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