# Computer Networks - Simple Web Proxy

A simple multi-threaded web proxy made for my Computer Networks class. Only works with HTTP connections (not HTTPS).

### web_proxy.py

The entire web proxy. `main()` will spin up a proxy that, by default, runs at `localhost:17771`. When the proxy receives a request, it will then send the request to a new thread through the `proxy_thread()` function, so it is able to handle multiple requests at the same time.