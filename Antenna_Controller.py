#Import necessary libraries
#import tkinter as tk
#from tkinter import filedialog as fd
import pyvisa as pv
import time
import threading
#import pandas as pd
#import matplotlib.pyplot as plt
#import numpy as np

# Send command to the device
def Send_Cmd(device, command):
    device.write(command)
# Read response of the device
def Read_Response(device):
    response = device.read()
    return response
#########################################################
def Initialize_AC(AC_Addr):
    rm = pv.ResourceManager()
    AC = rm.open_resource(AC_Addr)
    AC.baud_rate = 9600
    AC.data_bits = 8
    AC.parity = pv.constants.Parity.none
    AC.flow_control = pv.constants.VI_ASRL_FLOW_NONE
    AC.read_termination = '\n'
    AC.write_termination = '\n'
    AC.timeout = 20000  # Increase the timeout value
    return AC

# Waiting for Antenna to stop movement
Sim_Flag = False  # Set to True if running in simulation mode
Verbose = False  # Set to True for verbose output
def Wait_For_Stop(AC):
    Str_Rec = ""
    t = time.time()
    Sim_Counter = 0
    while Str_Rec != "0":
        if time.time() - t > 1:
            if Sim_Flag:
                if Sim_Counter == 5:
                    Str_Rec = "0"
                else:
                    Str_Rec = "1"
                Sim_Counter += 1
            else:
                Send_Cmd(AC, "BU")
                Str_Rec = Read_Response(AC)
            t = time.time()
        else:
            time.sleep(0.01)
            
# Function to change the polarization of the antenna
def Change_Polarization(AC, polarization):
    Send_Cmd(AC, "LD TMPM1 DV")
    if polarization == "vertical":
        Send_Cmd(AC, "PV")
    else:
        Send_Cmd(AC, "PH")

# Function to set the distance on the Antenna Controller
def Select_Distance(AC, distance):
    if distance == "3m":
        Send_Cmd(AC, "LD TMPM1 DV")
        Send_Cmd(AC, "LD 300 CM DYMD")
        Send_Cmd(AC, "LD DS1 DV")
    else:
        Send_Cmd(AC, "LD TMPM1 DV")
        Send_Cmd(AC, "LD 1000 CM DYMD")
        Send_Cmd(AC, "LD DT1 DV")
        
# Reset Height to 1m
def Reset_Height(AC):
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, "LD 100 CM NP")
    Send_Cmd(AC, "GO")

# Reset Turndisc Angle to 0 degrees
def Reset_Turndisc_Angle(AC):
    Send_Cmd(AC, "LD DS1 DV")
    Send_Cmd(AC, "LD 0 DG NP GO")

# Reset Turntable Angle to 0 degrees
def Reset_Turntable_Angle(AC):
    Send_Cmd(AC, "LD DT1 DV")
    Send_Cmd(AC, "LD 0 DG NP GO")

def start_polling_thread():
    polling_thread = threading.Thread(target=start_polling)
    polling_thread.daemon = True  # Daemonize the thread to exit when the main program exits
    polling_thread.start()

def query_position(AC):
    current_position = ""
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, "CP")
    response = Read_Response(AC)
    current_position = float(response)
    return current_position

def Reset_Height_After_Measurement(AC):
    p = 0
    Str_Rec = ""
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, "CP")
    Str_Rec = Read_Response(AC)
    p = float(Str_Rec)
    if p <= 200:
        Send_Cmd(AC, "LD 100 CM NP")
        Send_Cmd(AC, "GO")
    else:
        Send_Cmd(AC, "LD 400 CM NP")
        Send_Cmd(AC, "GO")