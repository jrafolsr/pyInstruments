# -*- coding: utf-8 -*-
"""
Created on Fri Oct 11 09:47:49 2019

@author: JOANRR

# min sampling interval is set by the socket sleeping time (0.1 s)

"""

from pyInstruments.pid_AK import TemperatureController
#from pyInstruments.pid import Pid
from threading  import Thread
from pyvisa import ResourceManager
import socket
import time
import re
import traceback


list_of_resources = ResourceManager().list_resources()
defult_resources = [s for s in list_of_resources if 'GPIB' in s]


#Parameters
setpoint = 20.0
heating = True
max_poutput = 12.0
multimeter_addr  = 'GPIB0::23::INSTR'
sourcemeter_addr = 'GPIB0::5::INSTR'
R0 = 100


#if __name__ == '__main__':
# Initialize the pid task
p = TemperatureController()
p.configurate(setpoint, heating, max_poutput, multimeter_addr, sourcemeter_addr, R0) 
p.pid_on()

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

# Set timeout to go over data receiving if not new set pont is transmitted
# client_socket.settimeout(0.1)
  

shut_down = True

# Start p.run as deamon thread while set temperatures are received
t1 = Thread(target = p.run)
t1.daemon = True
t1.start()
time.sleep(1)
i = 0
current_temperature = round(float(p.current_T),2)
while True:
    
    try:            
        # Receive request from client, could be SETting or READing the temperature
        received_data = client_socket.recv(1024)  
        received_data = received_data.decode("utf-8").strip()

        
        if "SET" in received_data:
            match = re.search(r'\d+\.\d+',received_data)
            received_value = float(match.group())
            p.setpoint = received_value
            #print(f'{i:05d} Received set temperature: {received_value}')
            
        if "READ?" in received_data:
            #somehow there is a bug reoccurng that the current T cannot be calculated properly
            #previous_temperature = current_temperature
            #try:
            current_temperature = round(float(p.current_T),2)
            client_socket.send(str(current_temperature).encode())
                
            #except:
            #    client_socket.send(str(previous_temperature).encode())
            
            #print(f'{i:05d} Sent current temperature: {current_temperature}')
            
        if 'output_off' in received_data:
            print('received order to turn off PID output')
            p.pid_off()
            
        if 'shut_down' in received_data:
            print('Client done sending')
            break
            
        if not received_data:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind to the IP and port
            server_socket.bind((host, port))
            server_socket.listen(1)
            print()
            print(f"Server listening on {host}:{port}...",end = '\n')
            client_socket, client_address = server_socket.accept()
            print()
            print(f"Connection established with {client_address}")        
        
    except KeyboardInterrupt:
        print('Program terminated by user')
        break
    
    except Exception as e:
        traceback.print_exc()
        print(e)
        print(f'The last easured R was {p.R}')
        print('No data received')
        
    i=i+1


if shut_down == False:
    input('Hit enter to safely terminate temperature approach')

# terminate the program safely
p.pid_off()
print(f'Terminated safely')

time.sleep(1)
# Close the connection
client_socket.close()
server_socket.close()

