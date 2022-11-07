import socket
import sys
from _thread import *


def proxy():
    imgSub, attack = 0, 1
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
            connection, _ = serverSocket.accept()

            data = connection.recv(8192)
            start_new_thread(conn_string, (connection, data, imgSub, attack))
        except KeyboardInterrupt:
            serverSocket.close()
            print("Shutting down server!")
            sys.exit(1)

    serverSocket.close()


def conn_string(connection, data, imgSub, attack):
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
            port = int(url[portPosition + 1:]
                       [:webserverPosition - portPosition - 1])
            webserver = url[:portPosition]

        print("LOG: Request received for webserver {} and port {}".format(
            webserver, port))
        proxy_server(webserver, port, connection, data, imgSub, attack)
    except Exception as err:
        # check for delimiter of \r\n???
        connection.send(b'400 - Bad Request')
        print("ERROR: Could not parse request from client", err)


def proxy_server(webserver, port, connection, data, imgSub, attack):
    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.connect((webserver, port))
        serverSocket.send(data)
        totalBytes = 0

        while True:
            if attack:
                HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Attack</title></head><body><p>You are being attacked.</p></body></html>"""
                connection.sendall(str.encode(
                    """HTTP/1.0 200 OK\n""", 'iso-8859-1'))
                connection.sendall(str.encode(
                    'Content-Type: text/html\n', 'iso-8859-1'))
                connection.send(str.encode('\n'))
                connection.sendall(str.encode(HTML, 'iso-8859-1'))
                print("LOG: You are under attack!")
                break

            reply = serverSocket.recv(8192)

            if len(reply) > 0:
                contentType = reply.find(b"Content-Type: image")

                if imgSub and contentType != -1:
                    print("LOG: Substituting image")
                    break

                #print("reply", reply.decode('utf-8'))
                connection.send(reply)
                totalBytes += len(reply)
                print("LOG: Reply of size {} received from {}".format(
                    len(reply), webserver))
            else:
                break

        print("LOG: Closing connection")
        if not attack:
            print("http://" + webserver.decode('utf-8'), totalBytes)
        serverSocket.close()
        connection.close()
    except Exception as err:
        print("ERROR: Could not forward request or reply", err)
        serverSocket.close()
        connection.close()
        sys.exit(1)


if __name__ == "__main__":
    proxy()
