import socket
import sys
from threading import Thread


def proxy():
    """
    Sets up the client socket based on the user inputs
    """
    port, imgSub, attack = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    try:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        clientSocket.bind(('192.168.51.86', port))
        clientSocket.listen(10)
    except Exception as err:
        sys.exit(2)

    hashmap = {}
    threads = []

    while True:
        while True:
            try:
                connection, _ = clientSocket.accept()
                data = connection.recv(1024)
                thread = Thread(target=receive_connection, args=(
                    connection, data, imgSub, attack, hashmap))
                thread.start()
                threads.append(thread)
                clientSocket.settimeout(2)
            except socket.timeout:
                break

            except KeyboardInterrupt:
                clientSocket.close()
                sys.exit(1)

        for thread in threads:
            # kills each thread and waits for them to terminate
            thread.join()

        if hashmap:
            for key in hashmap:
                print(f'http://{key.decode()}, {hashmap[key]}')

        hashmap, threads = {}, []


def receive_connection(connection, data, imgSub, attack, hashmap):
    """
    Receives a connection string and filters through its data
    """
    try:
        # checks before parsing
        # only dealing with HTTP 1 and GET
        if (data.find(b'HTTP/1.0') and data.find(b'HTTP/1.1')) == -1 or data.find(b'GET') == -1:
            raise Exception

        # gets the first part without headers
        # GET http://ocna0.d2.comp.nus.edu.sg:50000/tc1/ HTTP/1.1\r\n
        dataWithoutHeaders = data.split(b"\n")[0]
        # obtains url
        fullUrl = dataWithoutHeaders.split(b" ")[1]

        # getting rid of http in url
        httpPosition = fullUrl.find(b"://")
        url = fullUrl if httpPosition == -1 else fullUrl[httpPosition + 3:]

        portPosition = url.find(b":")
        webserverPosition = url.find(b"/")

        webserver = ""
        port = -1
        if webserverPosition == -1:
            webserverPosition = len(url)

        if portPosition == -1 or webserverPosition < portPosition:
            port = 80
            webserver = url[:webserverPosition]
        else:
            port = int(url[portPosition + 1:]
                       [:webserverPosition - portPosition - 1])
            webserver = url[:portPosition]

        # to get content length back in reply
        data = data.replace(b'HTTP/1.1', b'HTTP/1.0')
        proxy_server(webserver, port, connection,
                     data, imgSub, attack, hashmap)
    except Exception as err:
        HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Bad Request</title></head><body><center><h1>400 - Bad Request</h1></center></body></html>"""
        connection.sendall(str.encode(
            """HTTP/1.0 400 - Bad Request\n""", 'iso-8859-1'))
        connection.sendall(str.encode(
            'Content-Type: text/html\n', 'iso-8859-1'))
        connection.sendall(str.encode('\n'))
        connection.sendall(str.encode(HTML, 'iso-8859-1'))
        connection.close()


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
    totalBytes = 0

    while True:
        reply = b''
        try:
            reply += imgSocket.recv(1024)
        except socket.timeout:
            break

        if len(reply) > 0:
            contentLengthPosition = reply.find(b'Content-Length')
            validResPosition = reply.find(b'200 OK')
            if contentLengthPosition != -1 and validResPosition != -1:
                contentLength = reply[contentLengthPosition +
                                      16:].split(b'\r')[0]
                totalBytes += int(contentLength.decode())
            connection.sendall(reply)
        else:
            break

    imgSocket.close()
    return totalBytes


def read_reply(serverSocket, connection, imgSub):
    """
    Reads the reply from the server socket
    """
    totalBytes = 0
    while True:
        reply = b''
        try:
            reply += serverSocket.recv(1024)
        except socket.timeout:
            pass

        if len(reply) > 0:
            contentLengthPosition = reply.find(b'Content-Length')
            validResPosition = reply.find(b'200 OK')
            if contentLengthPosition != -1 and validResPosition != -1:
                contentLength = reply[contentLengthPosition +
                                      16:].split(b'\r')[0]
                totalBytes += int(contentLength.decode())
            # if image substitution enabled, make a new call to get it
            if imgSub and check_for_image(reply) != -1:
                serverSocket.close()
                totalBytes = send_img_sub(connection)
                break
            else:
                connection.sendall(reply)
        else:
            break
    return totalBytes


def proxy_server(webserver, port, connection, data, imgSub, attack, hashmap):
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
        hashmap[webserver] = hashmap.get(webserver, totalBytes)

        # if attack mode, we just want to send attack html
        if attack:
            send_attack(serverSocket, connection)
        else:
            bytesReceived = read_reply(
                serverSocket, connection, imgSub)
            hashmap[webserver] += bytesReceived

        serverSocket.close()
        connection.close()
    except Exception as err:
        serverSocket.close()
        connection.close()
        sys.exit(1)


if __name__ == "__main__":
    proxy()
