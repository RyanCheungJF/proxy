import socket
import sys
from _thread import *


def proxy():
    imgSub, attack = 0, 0
    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind(('', 8100))
        #serverSocket.bind((config['HOST_NAME'], config['BIND_PORT']))
        serverSocket.listen(10)
        print("LOG: Proxy started up!")
    except Exception as err:
        print("ERROR: Could not initialize socket with client", err)
        sys.exit(2)

    while True:
        try:
            connection, _ = serverSocket.accept()
            data = connection.recv(1024)
            start_new_thread(conn_string, (connection, data, imgSub, attack))
        except KeyboardInterrupt:
            serverSocket.close()
            print("Shutting down server!")
            sys.exit(1)


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
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((webserver, port))
        clientSocket.settimeout(1)
        clientSocket.sendall(data)
        # hardcoded size for attack reply
        totalBytes = 0 if not attack else 127

        while True:
            if attack:
                HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Attack</title></head><body><p>You are being attacked.</p></body></html>"""
                connection.sendall(str.encode(
                    """HTTP/1.0 200 OK\n""", 'iso-8859-1'))
                connection.sendall(str.encode(
                    'Content-Type: text/html\n', 'iso-8859-1'))
                connection.sendall(str.encode('\n'))
                connection.sendall(str.encode(HTML, 'iso-8859-1'))
                print("LOG: You are under attack!")
                break

            reply = b''
            try:
                reply += clientSocket.recv(1024)
            except socket.timeout:
                print

            if len(reply) > 0:
                contentType = reply.find(b"Content-Type: image")

                if imgSub and contentType != -1:
                    request = """GET http://ocna0.d2.comp.nus.edu.sg:50000/change.jpg HTTP/1.0\nHost ocna0.d2.comp.nus.edu.sg:50000\n"""
                    imgSocket = socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM)
                    imgSocket.connect(('ocna0.d2.comp.nus.edu.sg', 50000))
                    imgSocket.settimeout(1)
                    imgSocket.send(request.encode())

                    reply = b''
                    try:
                        reply += imgSocket.recv(1024)
                    except socket.timeout:
                        print

                    connection.send(reply)
                    totalBytes += len(reply)
                    imgSocket.close()
                    break

                connection.send(reply)
                totalBytes += len(reply)
                print("LOG: Reply of size {} received from {}".format(
                    len(reply), webserver))
            else:
                break

        print("LOG: Closing connection")
        print("http://" + webserver.decode('utf-8'), totalBytes)
        clientSocket.close()
        connection.close()
    except Exception as err:
        print("ERROR: Could not forward request or reply", err)
        clientSocket.close()
        connection.close()
        sys.exit(1)


if __name__ == "__main__":
    proxy()
