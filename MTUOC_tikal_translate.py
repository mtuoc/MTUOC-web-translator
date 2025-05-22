import os
import subprocess
import argparse
import codecs
import sys
import random
import requests
import re
from collections import Counter
import xml.etree.ElementTree as ET


class Tikal():
    def __init__(self):
        self.tikal_path=None
        self.sl="en"
        self.tl="es"
        self.segment=False
        self.srx_file=None
        self.okf=None
        
        self.ip="127.0.0.1"
        self.port=8000
        self.urlMTUOC= "http://"+self.ip+":"+str(self.port)+"/translate"
        self.strategy="segments"
        
    def set_path(self, path):
        self.tikal_path=path
        
    def set_sl(self, sl):
        self.sl=sl
        
    def set_tl(self, tl):
        self.tl=tl
        
    def set_srx_file(self, file):
        self.srx_file=file
        self.segment=True
    
    def set_okf(self, okf_filter):
        self.okf=okf_filter
        
    def set_ip(self, ip):
        self.ip=ip
        self.urlMTUOC= "http://"+self.ip+":"+str(self.port)+"/translate"
        
        
    def set_port(self, port):
        self.port=port
        self.urlMTUOC= "http://"+self.ip+":"+str(self.port)+"/translate"
        
        
           
    def translate(self, input_file):
        try:
            command = [self.tikal_path, '-t', input_file, '-sl', self.sl, '-tl',  self.tl]
            if self.segment:
                extension=['-seg',self.srx_file]
                command.extend(extension)
                
            if not self.okf==None:
                extension=['-fc',self.okf]
                command.extend(extension)
            self.transURL="http://"+str(self.ip)+":"+str(self.port)
            extension=['-mtuoc',self.transURL]
            command.extend(extension)
            # Run the command
            subprocess.run(command, check=True)
            #output_file=input_file+".xlf"
            #print(f"Successfully converted {input_file} to {output_file}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error during conversion: {e}")
        except FileNotFoundError:
            print("Error: Tikal executable not found. Please check the Tikal path.")
 
