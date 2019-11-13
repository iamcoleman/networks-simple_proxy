import os
import sys
import threading
import socket

"""
Global Variables for the Proxy
"""
QUEUE = 40                  # max number of pending connections
MAX_DATA_RECEIVE = 500000   # max number of bytes to receive at once
PORT_NUMBER = 17771         # port number of proxy
HOST = 'localhost'          # host of proxy
DEBUG = True                # True for debug messages


"""
Main Program
"""
def main():
    port = PORT_NUMBER  # port number set above
    host = HOST         # host set above

    print('Proxy Server running on {}:{}'.format('localhost', port))

    # create a socket
    try:
        proxSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxSocket.bind((host, port))
        proxSocket.listen(QUEUE)
    except:
        print('Could not open socket')
        sys.exit(1)

    # listen for connections from client
    while True:
        # establish the connection
        clientSocket, clientAddress = proxSocket.accept()

        # create a new thread for every request
        connectionThread = threading.Thread(target=proxy_thread, args=(clientSocket, clientAddress))
        connectionThread.setDaemon(True)
        connectionThread.start()


"""
Proxy Thread
"""
def proxy_thread(clientSocket, clientAddress):
    # receive the data
    clientRequest = clientSocket.recv(MAX_DATA_RECEIVE)

    if DEBUG:
        print('\nClient Request:')
        print(clientRequest)

    # parse the request
    first_line = clientRequest.split(b'\n')[0]
    url = b''
    if len(clientRequest) > 1:
        url = clientRequest.split(b' ')[1]

    if DEBUG:
        print('\nRequest First Line: {}'.format(first_line))
        print('Request URL: {}'.format(url))

    # find the webserver and the port
    http_pos = url.find(b'://')
    temp_web_server = url if http_pos < 0 else url[http_pos+3:]
    port_pos = temp_web_server.find(b':')
    web_server_pos = temp_web_server.find(b'/')
    if web_server_pos < 0:
        web_server_pos = len(temp_web_server)

    web_server = ''
    web_server_port = -1
    if port_pos < 0 or web_server_pos < port_pos:
        # default port
        web_server_port = 80
        web_server = temp_web_server[:web_server_pos]
    else:
        # specific port
        web_server_port = int(temp_web_server[port_pos + 1:][:web_server_pos - port_pos - 1])
        web_server = temp_web_server[:port_pos]

    if DEBUG:
        print('\nConnect to: {} {}'.format(web_server, web_server_port))

    # create a socket to connect to the web server
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((web_server, web_server_port))
        s.send(clientRequest)

        while True:
            # receive data from web server so send back to client
            try:
                data = s.recv(MAX_DATA_RECEIVE)
            except socket.timeout as e:
                err = e.args[0]
                # continue if timeout error
                if err == 'timed out':
                    print('\nError: recv timed out, retry later')
                    continue
                # kill proxy if another error
                else:
                    print('\nError: {}'.format(e))
                    sys.exit(1)
            except socket.error as e:
                print('\nError: {}'.format(e))
                sys.exit(1)

            if DEBUG:
                print('\nData Received: {}'.format(data))

            if len(data) > 0:
                # send to browser
                if DEBUG:
                    print('Sending to Browser: {}'.format(data))
                clientSocket.send(data)
            else:
                # connection is closed
                break

        # close both sockets
        s.close()
        clientSocket.close()
    except:
        print('Error: Unable to create socket')
        if s:
            s.close()
        if clientSocket:
            clientSocket.close()
        sys.exit(1)


if __name__ == '__main__':
    main()
