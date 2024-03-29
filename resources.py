# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 16:43:24 2019

@author: JOANRR
"""
import pyvisa as visa

class sourcemeter(object):
    def __init__(self, resource, termination = None):
        # Communicate with the resource and identify it
        self.resource = resource
        self.rm = visa.ResourceManager()
        if resource in self.rm.list_resources(): # Checking if the resource is available
            self.inst = self.rm.open_resource(resource)
            if self.inst.resource_info[3][:4] == 'ASRL':
                #This should be changed! gpib is also a instrument type
                if termination is not None:
                    self.inst.read_termination = termination
                    self.inst.write_termination = termination
                print('You have connected succesfully with an ASRL type resource')
            elif self.inst.resource_info[3][:4] == 'GPIB':
                print('You have connected succesfully with an GPIB type resource')
            elif self.inst.resource_info[3][:4] == 'USB0':
                print('You have connected succesfully with an USB0 type resource')
                pass
            else:
                raise Exception('Resource class not contemplated, check pyLab library')
#            self.inst.write("*RST")
            self.identify = self.inst.query("*IDN?")
        else:
            raise Exception("Resource not know, check your ports or NI MAX")
            
def list_resources():
    """Function that prints and returns a list with all the available resources in the PC. Needs the visa library from NI"""
    # List of the available resources
    resources = visa.ResourceManager().list_resources()
    print('Available resources in the PC:')
    print(resources)
    return resources