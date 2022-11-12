import socket
import sys
from _thread import *


def proxy():
    """
    Sets up the client socket based on the user inputs
    """
    imgSub, attack = 1, 0
    try:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.bind(('', 8100))
        #clientSocket.bind((config['HOST_NAME'], config['BIND_PORT']))
        clientSocket.listen(10)
        print("LOG: Proxy started up!")
    except Exception as err:
        print("ERROR: Could not initialize socket with client", err)
        sys.exit(2)

    while True:
        try:
            connection, _ = clientSocket.accept()
            data = connection.recv(1024)
            start_new_thread(receive_connection,
                             (connection, data, imgSub, attack))
        except KeyboardInterrupt:
            clientSocket.close()
            print("Shutting down server!")
            sys.exit(1)


def receive_connection(connection, data, imgSub, attack):
    """
    Receives a connection string and filters through its data
    """
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


def send_attack(clientSocket, connection):
    """
    Forms html to notify the user of attack mode
    """
    HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Attack</title></head><body><p>You are being attacked.</p></body></html>"""
    connection.sendall(str.encode(
        """HTTP/1.0 200 OK\n""", 'iso-8859-1'))
    connection.sendall(str.encode(
        'Content-Type: text/html\n', 'iso-8859-1'))
    connection.sendall(str.encode('\n'))
    connection.sendall(str.encode(HTML, 'iso-8859-1'))
    print("LOG: You are under attack!")
    clientSocket.close()
    connection.close()


def check_for_image(reply):
    """
    Checks if we are dealing with an image in the reply
    """
    return reply.find(b"Content-Type: image")


def send_img_sub(connection):
    """
    Requests the image to use as substitution and sends it back as a reply
    """
    # makes a get request to the endpoint to get the image
    request = """GET http://ocna0.d2.comp.nus.edu.sg:50000/change.jpg HTTP/1.0\r\n
        Host: ocna0.d2.comp.nus.edu.sg:50000\r\n""".encode()
    imgSocket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    imgSocket.connect(('ocna0.d2.comp.nus.edu.sg', 50000))
    imgSocket.settimeout(1)
    imgSocket.send(request)

    while True:
        reply = b''
        try:
            reply += imgSocket.recv(1024)
        except socket.timeout:
            break

        if len(reply) > 0:
            connection.sendall(reply)

    imgSocket.close()


def read_reply(serverSocket, connection, webserver, imgSub):
    """
    Reads the reply from the server socket
    """
    while True:
        reply = b''
        try:
            reply += serverSocket.recv(1024)
        except socket.timeout:
            pass

        if len(reply) > 0:
            # if image substitution enabled, make a new call to get it
            if imgSub and check_for_image(reply) != -1:
                serverSocket.close()
                send_img_sub(connection)
            else:
                connection.sendall(reply)
                #totalBytes += len(reply)
                print("LOG: Reply of size {} received from {}".format(
                    len(reply), webserver))
        else:
            break
    return 111


def proxy_server(webserver, port, connection, data, imgSub, attack):
    """
    Handles the requests from clients and replies from servers
    """
    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.connect((webserver, port))
        serverSocket.settimeout(1)
        serverSocket.sendall(data)
        # hardcoded size for attack reply
        totalBytes = 0 if not attack else 127

        # if attack mode, we just want to send attack html
        if attack:
            send_attack(serverSocket, connection)
        else:
            totalBytes = read_reply(
                serverSocket, connection, webserver, imgSub)

        print("LOG: Closing connection")
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
