# COMP9331 2019T2
# Date: 01/07/2019
# Lab 3 - WebServer.py
	# Basic TCP to run a simple web server

# Used Python 3

# NOTE: From my understanding of the specifications, I am not meant to close the connection socket and to keep it open indefinitely in the while loop

#coding: utf-8
from socket import *
import sys

try:
	serverPort = int(sys.argv[1])
except: # Port number required
	print ("Port number required")
	sys.exit()

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('localhost', serverPort))
serverSocket.listen(1)

while True:
	connectionSocket, addr = serverSocket.accept()
	sentence = connectionSocket.recv(1024)

	HTTP_Request = ''.join(chr(e) for e in sentence)
	request_line = (HTTP_Request.split('\n')[0]).split(' ') # Seperate and store request line of HTTP request
	if request_line[0] == 'GET': # Check if request is a GET request
		file_name = request_line[1][1:] # Get filename

	try:
		with open(file_name, 'rb') as file:
			html_response = "HTTP/1.1 200 OK\r\n"
			if file_name.split('.')[1] == 'html':
				html_response += "Content-Type: text/html; charset=ISO-8859-1\r\n"
			elif file_name.split('.')[1] == 'png':
				html_response += "Content-Type: image/png\r\n"
			html_response += "\r\n"

			connectionSocket.send(bytes(html_response, encoding = 'utf-8'))
			connectionSocket.sendfile(file)
	except:	# Send 404 Not Found response
		html_response = "HTTP/1.1 404 Not Found\r\n"
		html_response += "Content-Type: text/html; charset=ISO-8859-1\r\n"
		html_response += "\r\n"
		connectionSocket.send(bytes(html_response, encoding = 'utf-8'))
		Error_Message = '''
		<html>
		    <body>
				<center><h1>404 Not Found</h1></center>
		    </body>
		</html>
		'''
		connectionSocket.send(bytes(Error_Message, encoding = 'utf-8'))
