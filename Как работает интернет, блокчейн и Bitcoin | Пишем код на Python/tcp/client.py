from socket import *
import sys

host = 'localhost'
port = 9000
addr = (host,port)

tcp_socket = socket(AF_INET, SOCK_STREAM)
tcp_socket.connect(addr)


data = input('write to server: ')
if not data : 
    tcp_socket.close() 
    sys.exit(1)

#encode - перекодирует введенные данные в байты, decode - обратно
data = str.encode(data)
tcp_socket.send(data)
data = bytes.decode(data)
data = tcp_socket.recv(1024)
print(data)


tcp_socket.close()