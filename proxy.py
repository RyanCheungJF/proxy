import socket
import sys
from _thread import *

def proxy():
    try:
        print("Starting up...")
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind(('', 8100))
        #serverSocket.bind((config['HOST_NAME'], config['BIND_PORT']))
        serverSocket.listen(5)
        print("LOG: Proxy started up!")
    except Exception as err:
        print("ERROR: Could not initialize socket with client", err)
        sys.exit(2)

    while True:
        try:
            connection, addr = serverSocket.accept() 
            data = connection.recv(8192) 
            start_new_thread(conn_string, (connection, data, addr))
        except KeyboardInterrupt:
            serverSocket.close()
            print("Shutting down server!")
            sys.exit(1)
    
    serverSocket.close()
        
def conn_string(connection, data, addr):
    try:
        # gets the first part without headers
        # e.g b'CONNECT www.google.com:443 HTTP/1.1\r' (bytes format)
        dataWithoutHeaders = data.split(b"\n")[0]
        # obtains url
        fullUrl = dataWithoutHeaders.split(b" ")[1]

        # getting rid of http in url
        httpPosition = fullUrl.find(b"://")
        print("fullurl", fullUrl)
        url = fullUrl if httpPosition == -1 else fullUrl[httpPosition + 3:]

        portPosition = url.find(b":")
        webserverPosition = url.find(b"/")

        webserver = ""
        port = -1
        if webserverPosition == -1:
            webserverPosition = len(url)

        if portPosition == -1 or webserverPosition < portPosition:
            # probably should send 400?
            port = 80
            webserver = url[:webserverPosition]
        else:
            port = int(url[portPosition + 1:][:webserverPosition - portPosition - 1])
            webserver = url[:portPosition]
        
        print("LOG: Request received for webserver {} and port {}".format(webserver, port))
        proxy_server(webserver, port, connection, data, addr)
    except Exception as err:
        print("ERROR: Could not parse request from client", err)

def proxy_server(webserver, port, connection, data, addr):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.send(data)
        totalBytes = 0

        while True:
            reply = s.recv(8192)

            if len(reply) > 0:
                connection.send(reply)
                totalBytes += len(reply)
                print("LOG: Reply of size {} received from {}".format(len(reply), webserver))
            else:
                break
        
        print("http://" + webserver.decode('utf-8'), totalBytes)
        s.close()
        connection.close()
    except Exception as err:
        print("ERROR: Could not forward request or reply", err)
        s.close()
        connection.close()
        sys.exit(1)

if __name__== "__main__":
    proxy()