#Import necessary libraries
#import tkinter as tk
#from tkinter import filedialog as fd
#import pyvisa as pv
import time
#import pandas as pd
#import matplotlib.pyplot as plt
import numpy as np
import Antenna_Controller as AnCt
import Receiver as Rxr
import File_Data_and_Graphs as FDG

# Send command to the device
def Send_Cmd(device, command):
    device.write(command)
# Read response of the device
def Read_Response(device):
    response = device.read()
    return response
#######################################################
# Perform Height Scan with steps of 0.25 meters and store peak values in a dictionary
Sim_Flag = False  # Set to True if running in simulation mode
Verbose = False  # Set to True for verbose output
# def Ht_Scan_With_Peak(AC, Rx, Freq):
#     peak_ht_dict = {}
#     p = 0
#     Str_Rec = ""
#     if Sim_Flag:
#         if Verbose:
#             print("Tower scan height in progress... (Simulation)")
#         AnCt.Wait_For_Stop(AC)
#         return peak_ht_dict
#     Send_Cmd(AC, "LD TMPM1 DV")
#     Send_Cmd(AC, "CP")
#     Str_Rec = Read_Response(AC)
#     p = float(Str_Rec)
#     if p < 250:
#         for height in np.arange(100, 425, 25):
#             Send_Cmd(AC, f"LD {height:.2f} CM NP")
#             Send_Cmd(AC, "GO")
#             AnCt.Wait_For_Stop(AC)
#             # Read peak value from the receiver
#             Rxr.Set_Freq(Freq, Rx)
#             Pk_Value = Rxr.Get_Quasi_Peaks(Rx)
#             # Store the peak value and respective height in the dictionary
#             peak_ht_dict[height] = Pk_Value
#             # Initialize the traces in the receiver
#             Rxr.Initialize_Traces(Rx)
#         return peak_ht_dict
#     else:
#         for height in np.arange(400, 75, -25):
#             Send_Cmd(AC, f"LD {height:.2f} CM NP")
#             Send_Cmd(AC, "GO")
#             AnCt.Wait_For_Stop(AC)
#             # Read peak value from the receiver
#             Rxr.Set_Freq(Freq, Rx)
#             Pk_Value = Rxr.Get_Quasi_Peaks(Rx)
#             # Store the peak value and respective height in the dictionary
#             peak_ht_dict[height] = Pk_Value
#             # Initialize the traces in the receiver
#             Rxr.Initialize_Traces(Rx)
#         return peak_ht_dict

def query_position_AM(AC):
    current_position = ""
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, "CP")
    response = Read_Response(AC)
    current_position = float(response)
    return current_position

def Ht_Scan_With_Peak(AC, Rx, Freq):
    # ac_addr = "GPIB1::7::INSTR"
    # rx_addr = "USB0::0x2A8D::0x0F0B::MY59050129::0::INSTR"
    data_dict_ht = {}
    p = 0
    Str_Rec = ""
    # AC = Initialize_AC(ac_addr)
    # Rx = Initialize_Rx(rx_addr)
    Rxr.Set_Freq(Freq, Rx)
    #Rxr.Set_Quasi_Peaks(Rx)
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, "CP")
    Str_Rec = Read_Response(AC)
    p = float(Str_Rec)
    if p < 250:
        Send_Cmd(AC, "LD 400 CM NP")
        Send_Cmd(AC, "GO")
        while True:
            current_position = query_position_AM(AC)
            peak_value = Rxr.Get_Quasi_Peaks(Rx)
            # Display data in the text box
            data_dict_ht[current_position] = peak_value
            if current_position >= 389.7:
                break  # Exit the loop when the antenna reaches the target height
            #Rxr.Initialize_Traces(Rx)
            time.sleep(0.5)
        return data_dict_ht
    else:
        Send_Cmd(AC, "LD 100 CM NP")
        Send_Cmd(AC, "GO")
        while True:
            current_position = query_position_AM(AC)
            peak_value = Rxr.Get_Quasi_Peaks(Rx)
            # Display data in the text box
            data_dict_ht[current_position] = peak_value
            if current_position <= 100.1:
                break  # Exit the loop when the antenna reaches the target height
            #Rxr.Initialize_Traces(Rx)
            time.sleep(0.5)
        return data_dict_ht

def find_max_ht_peak(data_dict_ht):
    if not data_dict_ht:
        return None, None
    max_peak_value = -float('inf')
    max_peak_height = None
    for height, peak_value in data_dict_ht.items():
        if peak_value > max_peak_value:
            max_peak_value = peak_value
            max_peak_height = height
    return max_peak_value, max_peak_height

# Perform Angle Scan with steps of 5 degrees and store peak values in a dictionary
# def Angle_Scan_With_Peak(AC, Rx, Freq):
#     peak_ang_dict = {}
#     p = 0
#     Str_Rec = ""
#     if Sim_Flag:
#         if Verbose:
#             print("Angle scan in progress... (Simulation)")
#         AnCt.Wait_For_Stop(AC)
#         return peak_ang_dict
#     Send_Cmd(AC, "LD DS1 DV")
#     Send_Cmd(AC, "CP")
#     Str_Rec = Read_Response(AC)
#     p = float(Str_Rec)
#     if p < 1:
#         for angle in range(0, 361, 5):
#             # Move to the target angle in steps of 5 degrees
#             Send_Cmd(AC, f"LD {angle} DG NP GO")
#             AnCt.Wait_For_Stop(AC)
#             # Read peak value from the receiver
#             Rxr.Set_Freq(Freq, Rx)
#             Pk_Value = Rxr.Get_Quasi_Peaks(Rx)
#             # Store the peak value and respective angle in the dictionary
#             peak_ang_dict[angle] = Pk_Value
#             # Initialize the traces in the receiver
#             Rxr.Initialize_Traces(Rx)
#         return peak_ang_dict
#     else:
#         for angle in range(360, -1, -5):
#             # Move to the target angle in steps of 5 degrees
#             Send_Cmd(AC, f"LD {angle} DG NP GO")
#             AnCt.Wait_For_Stop(AC)
#             # Read peak value from the receiver
#             Rxr.Set_Freq(Freq, Rx)
#             Pk_Value = Rxr.Get_Quasi_Peaks(Rx)
#             # Store the peak value and respective angle in the dictionary
#             peak_ang_dict[angle] = Pk_Value
#             # Initialize the traces in the receiver
#             Rxr.Initialize_Traces(Rx)
#         return peak_ang_dict

def query_position_TD(AC):
    current_position = ""
    Send_Cmd(AC, "LD DS1 DV")
    Send_Cmd(AC, "CP")
    response = Read_Response(AC)
    current_position = float(response)
    return current_position

def Angle_Scan_With_Peak(AC, Rx, Freq):
    # ac_addr = "GPIB1::7::INSTR"
    # rx_addr = "USB0::0x2A8D::0x0F0B::MY59050129::0::INSTR"
    data_dict_ang = {}
    p = 0
    Str_Rec = ""
    # AC = Initialize_AC(ac_addr)
    # Rx = Initialize_Rx(rx_addr)
    Rxr.Set_Freq(Freq, Rx)
    #Rxr.Set_Quasi_Peaks(Rx)
    Send_Cmd(AC, "LD DS1 DV")
    Send_Cmd(AC, "CP")
    Str_Rec = Read_Response(AC)
    p = float(Str_Rec)
    if p < 1:
        Send_Cmd(AC, "LD 360 DG NP GO")
        Send_Cmd(AC, "GO")
        while True:
            current_position = query_position_TD(AC)
            peak_value = Rxr.Get_Quasi_Peaks(Rx)
            # Display data in the text box
            data_dict_ang[current_position] = peak_value
            if current_position >= 359.7:
                break  # Exit the loop when the antenna reaches the target height
            #Rxr.Initialize_Traces(Rx)
            time.sleep(0.5)
        return data_dict_ang
    else:
        Send_Cmd(AC, "LD 0 DG NP GO")
        Send_Cmd(AC, "GO")
        while True:
            current_position = query_position_TD(AC)
            peak_value = Rxr.Get_Quasi_Peaks(Rx)
            # Display data in the text box
            data_dict_ang[current_position] = peak_value
            if current_position <= 0.3:
                break  # Exit the loop when the antenna reaches the target height
            #Rxr.Initialize_Traces(Rx)
            time.sleep(0.5)
        return data_dict_ang

def find_max_ang_peak(data_dict_ang):
    if not data_dict_ang:
        return None, None
    max_peak_value = -float('inf')
    max_peak_angle = None
    for angle, peak_value in data_dict_ang.items():
        if peak_value > max_peak_value:
            max_peak_value = peak_value
            max_peak_angle = angle
    return max_peak_value, max_peak_angle
######################################################
def Auto_Measure(file_name):
    # Initialize the Antenna Controller and Receiver (Update the addresses accordingly)
    AC_Addr = 'GPIB1::7::INSTR'  # Update with the actual address of the Antenna Controller
    Rx_Addr = 'USB0::0x2A8D::0x0F0B::MY59050129::0::INSTR'  # Update with the actual address of the Receiver
    Rx = Rxr.Initialize_Rx(Rx_Addr)
    AC = AnCt.Initialize_AC(AC_Addr)

    # Lists to store data for writing to Excel later
    freq_list = []
    max_ht_list = []
    max_ang_list = []
    max_ht_height_list = []
    max_ang_angle_list = []

    # Perform scans for each frequency
    for freq in freqs:
        # Set the frequency on the Receiver
        #Rxr.Set_Freq(freq, Rx)

        # Perform Height Scan
        peak_ht_dict = Ht_Scan_With_Peak(AC, Rx, freq)
        max_ht_peak, max_ht_height = find_max_ht_peak(peak_ht_dict)
        FDG.write_ht_dict_to_excel(peak_ht_dict, freq, f'peak_ht_data_{freq:.2f}MHz.xlsx')
        
        # Bring the antenna to the height of the maximum peak
        Send_Cmd(AC, "LD TMPM1 DV")
        Send_Cmd(AC, f"LD {max_ht_height:.2f} CM NP")
        Send_Cmd(AC, "GO")
        AnCt.Wait_For_Stop(AC)

        # Perform Angle Scan
        peak_ang_dict = Angle_Scan_With_Peak(AC, Rx, freq)
        max_ang_peak, max_ang_angle = find_max_ang_peak(peak_ang_dict)
        FDG.write_ang_dict_to_excel(peak_ang_dict, freq, f'peak_ang_data_{freq:.2f}MHz.xlsx')
        
        # Store data for writing to Excel
        freq_list.append(freq)
        max_ht_list.append(max_ht_peak)
        max_ang_list.append(max_ang_peak)
        max_ht_height_list.append(max_ht_height)
        max_ang_angle_list.append(max_ang_angle)
        
        peak_values = []
        #save_list_to_csv(max_ht_height_list, 'peak_values.csv')
        # Compare angle peak and height peak and store the greater value in peak_values list
        for i in range(len(freq_list)):
            if max_ht_list[i] >= max_ang_list[i]:
                peak_values.append(max_ht_list[i])
            else:
                peak_values.append(max_ang_list[i])
        AnCt.Reset_Height_After_Measurement(AC)
    # Write data to Excel
    FDG.Write_To_Excel(file_name, freq_list, max_ht_height_list, max_ht_list, max_ang_angle_list, max_ang_list, peak_values)

    # Close the connection to the Antenna Controller and Receiver
    AC.close()
    Rx.close()

    # Plot graphs
    FDG.plot_max_peak_vs_freq(freq_list, peak_values)
    #FDG.plot_height_vs_peak(max_ht_list, max_ht_height_list)
    #FDG.plot_angle_vs_peak_polar(max_ang_peak, max_ang_angle_list, max_ang_list)