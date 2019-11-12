import os
import sys
import threading
import socket

"""
Variables for the Proxy
"""
QUEUE = 25                  # max number of pending connections
MAX_DATA_RECEIVE = 500000   # max number of bytes to receive at once
PORT_NUMBER = 17771         # port number of proxy
DEBUG = True                # True for debug messages


"""
Main Program
"""
def main():
    port = PORT_NUMBER  # port number set above
    host = ''           # blank for `localhost`

    print('Proxy Server running on {}:{}'.format('localhost', port))

    # create a socket
    try:
        proxSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxSocket.bind((host, port))
        proxSocket.listen(QUEUE)
    except:
        print('Could not open socket')
        return

    # listen for connections from client
    while True:
        # establish the connection
        clientSocket, clientAddress = proxSocket.accept()

        # create a thread for every request
        connectionThread = threading.Thread(target=proxy_thread, args=(clientSocket, clientAddress))
        connectionThread.setDaemon(True)
        connectionThread.start()


"""
Proxy Thread
"""
def proxy_thread(clientSocket, clientAddress):
    # receive the data
    clientRequest = clientSocket.recv(MAX_DATA_RECEIVE)
    print(clientRequest)

    # parse the request
    first_line = clientRequest.split(b'\n')[0]
    url = clientRequest.split(b' ')[1]

    if DEBUG:
        print('First Line: {}'.format(first_line))
        print('URL: {}'.format(url))

    # find the webserver and the port
    http_pos = url.find(b'://')
    temp = url if http_pos < 0 else url[http_pos+3:]
    port_pos = temp.find(b':')
    webserver_pos = temp.find(b'/')
    if webserver_pos < 0:
        webserver_pos = len(temp)

    webserver = ''
    port = -1
    if port_pos < 0 or webserver_pos < port_pos:
        # default port
        port = 80
        webserver = temp[:webserver_pos]
    else:
        # specific port
        port = int(temp[port_pos+1:][:webserver_pos-port_pos-1])
        webserver = temp[:port_pos]

    if DEBUG:
        print('Connect to: {} {}'.format(webserver, port))

    # create a socket to connect to the web server
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.send(clientRequest)

        while True:
            # receive data from web server
            try:
                data = s.recv(MAX_DATA_RECEIVE)
            except socket.timeout as e:
                err = e.args[0]
                if err == 'timed out':
                    print('recv timed out, retry later')
                    continue
                else:
                    print('Error: {}'.format(e))
                    sys.exit(1)
            except socket.error as e:
                print('Error: {}'.format(e))
                sys.exit(1)

            if DEBUG:
                print('Data: {}'.format(data))

            if len(data) > 0:
                # send to browser
                if DEBUG:
                    print('Sending to browser: {}'.format(data))
                clientSocket.send(data)
            else:
                # connection is closed
                break

        # close both sockets
        s.close()
        clientSocket.close()
    except:
        print('Unable to create socket')
        if s:
            s.close()
        if clientSocket:
            clientSocket.close()
        sys.exit(1)


if __name__ == '__main__':
    main()
