# -*- coding: utf-8 -*-
"""
Created on Fri Oct 11 09:47:49 2019

@author: JOANRR

"""

from pyInstruments.pid_AK import TemperatureController
#from pyInstruments.pid import Pid
from threading  import Thread
from pyvisa import ResourceManager
import socket

# Set up a TCP server that provides temperature values va Ethernet
host = '0.0.0.0'  # Listen on all available interfaces (use 'localhost' or '127.0.0.1' if only on local network)
port = 8060       # Port to listen on

# Create a socket object and enable address reuse
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind to the IP and port
server_socket.bind((host, port))
server_socket.listen(1)

print(f"Server listening on {host}:{port}...")

# Accept a connection from the laptop
client_socket, client_address = server_socket.accept()
print(f"Connection established with {client_address}")
    
