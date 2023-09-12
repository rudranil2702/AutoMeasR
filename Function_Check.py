# import tkinter as tk
# from tkinter import filedialog
import pyvisa as pv
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def Send_Cmd(device, command):
    device.write(command)
# Read response of the device
def Read_Response(device):
    response = device.read()
    return response

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

def Read_From_Excel(File_Name):
    df = pd.read_excel(File_Name)
    Freqs = df.iloc[:, 0].tolist()
    return Freqs

def Read_Reference_Values(file_name):
    df = pd.read_excel(file_name)
    reference_values = df.iloc[:, 1].tolist() # read from col2
    return reference_values

def Write_Peak_Values_to_Excel(file_name, frequencies, peak_values):
    df = pd.read_excel(file_name)
    df['Peak Values [dBuV]'] = peak_values
    df.to_excel(file_name, index=False)

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
    
def Get_Peak_Value(mxe_rxr):
    #mxe_rxr.write(":CALC:MARK:AVER")
    mxe_rxr.write(":CALC:MARK2:Y?")
    response = mxe_rxr.read()
    amp = float(response)
    return amp

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
    Set_Freq(Freq, Rx)
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
            peak_value = Get_Peak_Value(Rx)
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
            peak_value = Get_Peak_Value(Rx)
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

def linearize_curve(peak_values, reference_values):
    linearized_values = peak_values-reference_values
    return linearized_values

def start_processing(FC_File_Name):
    #file_name = entry_file.get()
    rx_address = input("Enter the Receiver address: ")
    ac_address = input("Enter the Antenna Controller GPIB address: ")
    frequencies = Read_From_Excel(FC_File_Name)
    mxe_rxr = Initialize_Rx(rx_address)
    ac = Initialize_AC(ac_address)

    peak_values = []
    for frequency in frequencies:
        Set_Freq(frequency, mxe_rxr)
        Ht_Scan_With_Peak(ac)
        #mxe_rxr.write(":CALC:MARK:MAX:STAT ON")
        # Perform a single measurement using Max Hold
        peak_value = Get_Peak_Value(mxe_rxr)
        # Disable Max Hold feature
        #mxe_rxr.write(":CALC:MARK:MAX:STAT OFF")
        peak_values.append(peak_value)

    Write_Peak_Values_to_Excel(FC_File_Name, frequencies, peak_values)
    reference_values = Read_Reference_Values(FC_File_Name)
    linearized_reference_values = linearize_curve(reference_values)
    linearized_peak_values = linearize_curve(peak_values)
    ac.close()
    mxe_rxr.close()
####################################################################################################################################################
    upper_limit = np.mean(np.array(reference_values)) + 3
    lower_limit = np.mean(np.array(reference_values)) - 3
    linearized_upper_limit = np.array(linearized_reference_values) + 3
    linearized_lower_limit = np.array(linearized_reference_values) - 3

    #label_status.config(text="Processing completed!")

    plt.semilogx(frequencies, linearized_peak_values, marker='.', linestyle='-', color='navy', label='Peak Values', linewidth=2)
    plt.semilogx(frequencies, linearized_reference_values, marker='.', linestyle='-', color='green', label='Reference Values', linewidth=2)
    plt.semilogx(frequencies, linearized_upper_limit, linestyle='--', color='maroon', label='Limit Line at +/-3dB', linewidth=1)
    plt.semilogx(frequencies, linearized_lower_limit, linestyle='--', color='maroon', linewidth=1)
    plt.xlabel('Frequency [MHz]')
    plt.ylabel('Peak Values [dBuV]')
    plt.legend()
    plt.grid(True)

    plt.semilogx(frequencies, peak_values, marker='.', linestyle='-', color='navy', label='Peak Values', linewidth=2)
    plt.semilogx(frequencies, reference_values, marker='.', linestyle='-', color='green', label='Reference Values', linewidth=2)
    plt.semilogx(frequencies, upper_limit, linestyle='--', color='maroon', label='Limit Line at +/-3dB', linewidth=1)
    plt.semilogx(frequencies, lower_limit, linestyle='--', color='maroon', linewidth=1)
    plt.xlabel('Frequency [MHz]')
    plt.ylabel('Peak Values [dBuV]')
    plt.legend()
    plt.grid(True)
    plt.show()
# # Set simulation flag and verbosity
# SimFlag = False  # Set to True if running in simulation mode
# Verbose = False  # Set to True for verbose output

# Antenna Controller Functions

# def ConfigureGPIBCommunication(ac_address):
#     rm = pyvisa.ResourceManager()
#     ac = rm.open_resource(ac_address)
#     ac.baud_rate = 9600
#     ac.data_bits = 8
#     ac.parity = pyvisa.constants.Parity.none
#     ac.flow_control = pyvisa.constants.VI_ASRL_FLOW_NONE
#     ac.read_termination = '\n'
#     ac.write_termination = '\n'
#     ac.timeout = 20000  # Increase the timeout value
#     return ac

# def SendCmd(ac, command):
#     ac.write(command)

# def ReadResponse(ac):
#     response = ac.read()
#     return response

# def WaitForStop(ac):
#     strRec = ""
#     t = time.time()
#     SimCounter = 0
#     while strRec != "0":
#         if time.time() - t > 1:
#             if SimFlag:
#                 if SimCounter == 5:
#                     strRec = "0"
#                 else:
#                     strRec = "1"
#                 SimCounter += 1
#             else:
#                 Send_Cmd(ac, "BU")
#                 strRec = Read_Response(ac)

#             t = time.time()
#         else:
#             time.sleep(0.001)

# def Scan(ac):
#     p = 0
#     strRec = ""
#     if SimFlag:
#         if Verbose:
#             print("Tower scan height in progress... (Simulation)")
#         WaitForStop(ac)
#         return
#     SendCmd(ac, "LD TMPM1 DV")
#     SendCmd(ac, "CP")
#     strRec = ReadResponse(ac)
#     p = float(strRec)
#     if 100.4 < p < 399:
#         if p < 250:
#             SendCmd(ac, "LD 100 CM NP")
#             SendCmd(ac, "GO")
#             p = 100
#         else:
#             SendCmd(ac, "LD 400 CM NP")
#             SendCmd(ac, "GO")
#             p = 400
#         WaitForStop(ac)
#     if p < 100.6:
#         SendCmd(ac, "LD 400 CM NP")
#         SendCmd(ac, "GO")
#     else:
#         SendCmd(ac, "LD 100 CM NP")
#         SendCmd(ac, "GO")

#     WaitForStop(ac)

# Receiver Functions

# def read_excel_file(file_name):
#     df = pd.read_excel(file_name)
#     frequencies = df.iloc[:, 0].tolist()
#     return frequencies

# def initialize_mxe_rxr(rx_address):
#     rm = pyvisa.ResourceManager()
#     mxe_rxr = rm.open_resource(rx_address)
#     #mxe_rxr.write(":BAND:RES 120 kHz")
#     #mxe_rxr.write(":TRACe:MODE MAXHold")
#     mxe_rxr.write("*RCL 6")
#     #mxe_rxr.timeout = 20000
#     return mxe_rxr

# def set_frequency(frequency, mxe_rxr):
#     freq_in_hz = frequency * 1e6
#     mxe_rxr.write(f":FREQ:CENT {freq_in_hz} Hz")

# # GUI Functions
# def browse_file():
#     file_name = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xlsm")])
#     if file_name:
#         entry_file.delete(0, tk.END)
#         entry_file.insert(0, file_name)

# def start_processing(FC_File_Name):
#     #file_name = entry_file.get()
#     rx_address = input("Enter the Receiver address: ")
#     ac_address = input("Enter the Antenna Controller GPIB address: ")
#     frequencies = read_excel_file(FC_File_Name)
#     mxe_rxr = initialize_mxe_rxr(rx_address)
#     ac = ConfigureGPIBCommunication(ac_address)

#     peak_values = []
#     for frequency in frequencies:
#         set_frequency(frequency, mxe_rxr)
#         Scan(ac)
#         #mxe_rxr.write(":CALC:MARK:MAX:STAT ON")
#         # Perform a single measurement using Max Hold
#         peak_value = get_peak_value(mxe_rxr)
#         # Disable Max Hold feature
#         #mxe_rxr.write(":CALC:MARK:MAX:STAT OFF")
#         peak_values.append(peak_value)

#     write_peak_values_to_excel(FC_File_Name, frequencies, peak_values)
#     reference_values = read_reference_values(FC_File_Name)
#     linearized_reference_values = linearize_curve(reference_values)
#     linearized_peak_values = linearize_curve(peak_values)
#     ac.close()
#     mxe_rxr.close()
# ####################################################################################################################################################
#     upper_limit = np.mean(np.array(reference_values)) + 3
#     lower_limit = np.mean(np.array(reference_values)) - 3
#     linearized_upper_limit = np.array(linearized_reference_values) + 3
#     linearized_lower_limit = np.array(linearized_reference_values) - 3

#     #label_status.config(text="Processing completed!")

#     plt.semilogx(frequencies, linearized_peak_values, marker='.', linestyle='-', color='navy', label='Peak Values', linewidth=2)
#     plt.semilogx(frequencies, linearized_reference_values, marker='.', linestyle='-', color='green', label='Reference Values', linewidth=2)
#     plt.semilogx(frequencies, linearized_upper_limit, linestyle='--', color='maroon', label='Limit Line at +/-3dB', linewidth=1)
#     plt.semilogx(frequencies, linearized_lower_limit, linestyle='--', color='maroon', linewidth=1)
#     plt.xlabel('Frequency [MHz]')
#     plt.ylabel('Peak Values [dBuV]')
#     plt.legend()
#     plt.grid(True)

#     plt.semilogx(frequencies, peak_values, marker='.', linestyle='-', color='navy', label='Peak Values', linewidth=2)
#     plt.semilogx(frequencies, reference_values, marker='.', linestyle='-', color='green', label='Reference Values', linewidth=2)
#     plt.semilogx(frequencies, upper_limit, linestyle='--', color='maroon', label='Limit Line at +/-3dB', linewidth=1)
#     plt.semilogx(frequencies, lower_limit, linestyle='--', color='maroon', linewidth=1)
#     plt.xlabel('Frequency [MHz]')
#     plt.ylabel('Peak Values [dBuV]')
#     plt.legend()
#     plt.grid(True)
#     plt.show()
    
# # UI Design

# window = tk.Tk()
# window.title("Function Test")
# window.geometry("400x250")
# window.configure(bg="#333333")

# label_file = tk.Label(window, text="Select Excel File:", fg="#FFFFFF", bg="#333333", font=("Arial", 12))
# label_file.pack(pady=10)

# file_frame = tk.Frame(window, bg="#333333")
# file_frame.pack()

# entry_file = tk.Entry(file_frame, font=("Arial", 12))
# entry_file.pack(side=tk.LEFT, padx=5)

# button_browse = tk.Button(file_frame, text="Browse", font=("Arial", 12), command=browse_file)
# button_browse.pack(side=tk.RIGHT, padx=5)

# button_start = tk.Button(window, text="Start Processing", font=("Arial", 12), command=start_processing)
# button_start.pack(pady=10)

# label_status = tk.Label(window, text="", fg="#FFFFFF", bg="#333333", font=("Arial", 12))
# label_status.pack()

# button_quit = tk.Button(window, text="Exit", font=("Arial", 12), command=window.quit)
# button_quit.pack(anchor=tk.SE, pady=10)

# #button_start = tk.Button(window, text="Reset", font=("Arial", 12), command=check_reset_conditions)
# #button_start.pack(pady=10)

# window.mainloop()