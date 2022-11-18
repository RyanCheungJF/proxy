# HTTP 1 Proxy

This proxy is meant to be ran on Firefox 92 and has added functionality such as 
image substitution, attack mode flagging and telemetry support.
Currently, it only supports HTTP 1.0 or HTTP 1.1 and only GET requests.

To run the proxy, use the following command:
```
python3 proxy.py <port> <imagesub> <attack>

e.g
python3 proxy.py 8100 0 0

or

python3 proxy.py 8100 1 0
```

Do ensure that the arguments are separated by a space, 
and run this in the directory where `proxy.py` resides in.

### Arguments

`port`: Takes in any value

`imagesub`: 
- `0`: Does not substitute any image
- `1`: Substitues all images on the webpage

`attack`:
- `0`: Does not attack and renders normally
- `1`: For all requests, a special HTML is rendered, 
showing that you are being attacked.

### Telemetry

After each request, the telemetry support will print out the size of all resources for the request.