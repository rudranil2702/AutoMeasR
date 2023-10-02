#Import necessary libraries
#import tkinter as tk
#from tkinter import filedialog as fd
import pyvisa as pv
import time
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
#######################################################
# Initialize Receiver
def Initialize_Rx(Rx_Addr):
    rm = pv.ResourceManager()
    Rx = rm.open_resource(Rx_Addr)
    #Send_Cmd(Rx, ":BAND:RES 120 kHz")
    #Send_Cmd(Rx, ":UNIT:POW dBuV") 
    Send_Cmd(Rx, "*RCL 6")
    #Send_Cmd(Rx, ":INST:SEL EMI")
    #Send_Cmd(Rx, ":FREQ:SPAN 0 Hz")
    #Send_Cmd(Rx, "SWE:TIME 10 s")
    return Rx

# def Initialize_Rx_MaxHold(Rx_Addr):
#     rm = pv.ResourceManager()
#     Rx = rm.open_resource(Rx_Addr)
#     Send_Cmd(Rx, ":BAND:RES 120 kHz")
#     Send_Cmd(Rx, ":TRACe:MODE MAXH")  # Set trace mode to max hold
#     Send_Cmd(Rx, ":UNIT:POW dBuV")  # Set amplitude unit to dBµV
#     return Rx

# def Set_Trace_Type(Rx, trace_num, trace_type):
#     Send_Cmd(Rx, f"TRAC{trace_num}:TYPE {trace_type}")

# Set center frequency
def Set_Freq(Freq, Rx):
    Freq_Hz = Freq * 1e6
    #Send_Cmd(Rx, ":FREQ:SPAN 0 Hz")
    Send_Cmd(Rx, f":FREQ:CENT {Freq_Hz} Hz")
    #Send_Cmd(Rx, f":CALC:MARK1:X {Freq_Hz} Hz\n")
    Send_Cmd(Rx, ":CALC:MARK1 ON")
    Send_Cmd(Rx, ":CALC:MARK1:X 0")
    Send_Cmd(Rx, ":CALC:MARK2:X 0")
    Send_Cmd(Rx, ":CALC:MARK2 ON")
    Send_Cmd(Rx, ":CALC:MARK3:X 0")
    Send_Cmd(Rx, ":CALC:MARK3 ON")
    
def Set_Quasi_Peaks(Rx):
    #Send_Cmd(Rx, "DET:TRAC1 QPE")
    #Send_Cmd(Rx, ":CALC:MAM:DET QPE")
    #Send_Cmd(Rx, ":FREQ:SPAN 0 Hz")
    Send_Cmd(Rx, "TRAC1:TYPE WRIT")#":DET QPE")
    Send_Cmd(Rx, "DET:TRAC1 QPE")
    Send_Cmd(Rx, "TRAC2:TYPE WRIT")#:DET QPE")
    Send_Cmd(Rx, "DET:TRAC2 QPE")
    Send_Cmd(Rx, "DET:TRAC3 QPE")
    Send_Cmd(Rx, "SENS:BAND 750e3")
    Send_Cmd(Rx, "SENS:SWE:TIME 20")
    Send_Cmd(Rx, ":CALC:MARK:CPS ON")
    Send_Cmd(Rx, ":CALC:MARK:TRCK OFF")

def Get_Quasi_Peaks(Rx):
    peaks = []
    for _ in range(3):  # Perform marker updates (adjust as needed)
        #Initialize_Traces(Rx)
        #Set_Marker_To_Maximum(Rx)
        #Initialize_Traces(Rx)
        #time.sleep(1)
        peak = Get_Continuous_Peak(Rx)
        peaks.append(peak)
        #print(f"Frequency: {Freq} MHz, Peak: {peak}")
        time.sleep(.05)  # Delay between marker updates (adjust as needed)
    # Send_Cmd(Rx, ":CALC:MARK:MAX")
    # Send_Cmd(Rx, ":CALC:MARK:Y?")
    # response = Read_Response(Rx)
    QPk = max(peaks)
    # Initialize_Traces(Rx)
    return QPk

def Get_Continuous_Peak(Rx):
    #Send_Cmd(Rx, ":INIT:CONT ON")
    #Send_Cmd(Rx, ":CALC:MARK3:MAX")
    Send_Cmd(Rx, ":CALC:MARK2:Y?")
    response = Read_Response(Rx)
    peak = float(response)
    #Initialize_Traces(Rx)
    return peak

# Get peak values
def Get_Max_Peaks(Rx):
    #Send_Cmd(Rx, "MARK:TRAC1:TYPE MAXH")
    Send_Cmd(Rx, ":CALC:MARK:MAX")
    Send_Cmd(Rx, ":CALC:MARK:Y?")
    response = Read_Response(Rx)
    Pk = float(response)
    return Pk
# Check this: CALC:MARK1:TRAC 2

def Get_Average_Peaks(Rx):
    Send_Cmd(Rx, "MARK2:TRAC2:TYPE AVER")
    Send_Cmd(Rx, ":CALC:MAM:DET AVER")
    Send_Cmd(Rx, ":CALC:MARK2:Y?")
    response = Read_Response(Rx)
    Avg = float(response)
    return Avg

# Init Traces
# def Initialize_Traces(Rx):
#     #Send_Cmd(Rx, "CLRW TRA;CLRW TRB;MXMH TRA;")
#     Send_Cmd(Rx, ":INIT:CONT ON") #try cont off
#     Send_Cmd(Rx, "TRAC1:TYPE WRIT")
#     #Send_Cmd(Rx, ":TRACe:CLEar:ALL")
#     #Send_Cmd(Rx, "TRAC5:TYPE WRIT")
#     #:TRACe:CLEar TRACE1|TRACE2|TRACE3
    
def Set_Measurement_Mode(Rx, mode):
    #Initialize_Rx()
    if mode == "Emi Receiver":
        Send_Cmd(Rx, ":INST:SEL EMI")
    else:
        Send_Cmd(Rx, ":INST:SEL SA")
        
def recall_receiver_state(receiver, state_name):
    # Send the SCPI command to recall the state by name
    command = f":INST:STAT:RES '{state_name}'"
    receiver.write(command)
    receiver.query("*OPC?")  # Wait for operation to complete (no error checking)
