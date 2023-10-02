import tkinter as tk
from tkinter import filedialog as fd
#import pyvisa as pv
#import time
import pandas as pd
import matplotlib.pyplot as plt
#import numpy as np

import Antenna_Controller as AnCt
import Receiver as Rxr
import File_Data_and_Graphs as FDG
import Measurement as MM
import Function_Check as FC

# Send command to the device
def Send_Cmd(device, command):
    device.write(command)
# Read response of the device
def Read_Response(device):
    response = device.read()
    return response

window = tk.Tk()
window.title("Radiated Emissions Measurement Software")
window.geometry("1280x720")
window.configure(bg="#333333")

# Antenna Controller Section
ac_frame = tk.Frame(window, bg="#333333")
ac_frame.pack(side="left", padx=20, pady=20, anchor="nw")

tk.Label(ac_frame, text="Antenna Controller", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="center")

ac_address_frame = tk.Frame(ac_frame, bg="#333333")
ac_address_frame.pack(anchor="w")
tk.Label(ac_address_frame, text="Address:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
ac_address_entry = tk.Entry(ac_address_frame)
ac_address_entry.pack(side="left")
ac_address_entry.insert(0, "GPIB1::7::INSTR")  # Default value
def initialize_antenna_controller():
    AC_Addr = ac_address_entry.get()
    AC = AnCt.Initialize_AC(AC_Addr)
    # You can perform additional initialization or configuration here
    return AC
ac_init_button = tk.Button(ac_address_frame, text="Initialize", command=initialize_antenna_controller)
ac_init_button.pack(padx=(5, 0))

# Polarization Options
polarization_frame = tk.Frame(ac_frame, bg="#333333", pady=10)
polarization_frame.pack(anchor="w")
tk.Label(polarization_frame, text="Polarization:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left", padx=(0, 10))
polarization_var = tk.StringVar()
polarization_var.set("horizontal")  # Default value
tk.Radiobutton(polarization_frame, text="Vertical", variable=polarization_var, value="vertical", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
tk.Radiobutton(polarization_frame, text="Horizontal", variable=polarization_var, value="horizontal", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
def Set_Polarization():
    # Initialize the Antenna Controller (Update the address accordingly)
    AC_Addr = ac_address_entry.get() # Update with the actual address of the Antenna Controller
    AC = AnCt.Initialize_AC(AC_Addr)
    # Get the selected polarization from the UI
    selected_polarization = polarization_var.get()
    # Change polarization using the new function
    AnCt.Change_Polarization(AC, selected_polarization)
    # Close the connection to the Antenna Controller
    AC.close()
# Set Button
set_polarization_button = tk.Button(ac_frame, text="Set Polarization", command=Set_Polarization)
set_polarization_button.pack(anchor="e", padx=(5, 0))

# Distance of Test Options
distance_frame = tk.Frame(ac_frame, bg="#333333", pady=10)
distance_frame.pack(anchor="w")
tk.Label(distance_frame, text="Distance of Test:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left", padx=(0, 10))
distance_var = tk.StringVar()
distance_var.set("3m")  # Default value
tk.Radiobutton(distance_frame, text="3m (Turndisc)", variable=distance_var, value="3m", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
tk.Radiobutton(distance_frame, text="10m (Turntable)", variable=distance_var, value="10m", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
def Set_Distance():
    # Initialize the Antenna Controller (Update the address accordingly)
    AC_Addr = ac_address_entry.get()  # Update with the actual address of the Antenna Controller
    AC = AnCt.Initialize_AC(AC_Addr)
    # Get the selected distance from the UI
    selected_distance = distance_var.get()
    # Set the distance using the new function
    AnCt.Select_Distance(AC, selected_distance)
    # Close the connection to the Antenna Controller
    AC.close()
set_distance_button = tk.Button(ac_frame, text="Set Distance", command=Set_Distance)
set_distance_button.pack(anchor="e", padx=(5, 0))#, pady = 10)

height_go_frame = tk.Frame(ac_frame, bg="#333333", pady=10)
height_go_frame.pack(anchor="w")
height_label = tk.Label(height_go_frame, text="Height (meters):", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")#, padx=(0, 10))
height_entry = tk.Entry(height_go_frame)
height_entry.pack(side="left")
def go_to_height():
    AC_Addr = ac_address_entry.get()  # Update with the actual address of the Antenna Controller
    AC = AnCt.Initialize_AC(AC_Addr)
    height = float(height_entry.get())
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, f"LD {height} CM NP")
    Send_Cmd(AC, "GO")
# Create a button to trigger "Go to Height"
go_height_button = tk.Button(height_go_frame, text="Go", command=go_to_height)
go_height_button.pack(padx=(5, 0))

# Create a label and entry for entering the angle
angle_go_frame = tk.Frame(ac_frame, bg="#333333")#, pady=5)
angle_go_frame.pack(anchor="w")
angle_label = tk.Label(angle_go_frame, text="Angle (degrees):", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")#, padx=(0, 10))
angle_entry = tk.Entry(angle_go_frame)
angle_entry.pack(side="left")
def go_to_angle():
    AC_Addr = ac_address_entry.get()  # Update with the actual address of the Antenna Controller
    AC = AnCt.Initialize_AC(AC_Addr)
    angle = float(angle_entry.get())
    Send_Cmd(AC, "LD DT1 DV")
    Send_Cmd(AC, f"LD {angle} DG NP GO")
# Create a button to trigger "Go to Angle"
go_angle_button = tk.Button(angle_go_frame, text="Go", command=go_to_angle)
go_angle_button.pack(padx=(5, 0))

reset_frame = tk.Frame(ac_frame, bg="#333333", pady=10)
reset_frame.pack(anchor="w")
# Reset Height Button
def Reset_Height_UI():
    # Initialize the Antenna Controller (Update the address accordingly)
    AC_Addr = ac_address_entry.get()
    AC = AnCt.Initialize_AC(AC_Addr)
    # Call the Reset_Height function and pass the AC object
    AnCt.Reset_Height(AC)
    # Close the connection to the Antenna Controller
    AC.close()
reset_height_button = tk.Button(reset_frame, text="Reset Height to 1m", command=Reset_Height_UI)
reset_height_button.pack(anchor="w", padx=(5, 0), pady=5)

# Reset Turndisc Angle Button
def Reset_Turndisc_Angle_UI():
    # Initialize the Antenna Controller (Update the address accordingly)
    AC_Addr = ac_address_entry.get()
    AC = AnCt.Initialize_AC(AC_Addr)
    # Call the Reset_Height function and pass the AC object
    AnCt.Reset_Turndisc_Angle(AC)
    # Close the connection to the Antenna Controller
    AC.close()
reset_turndisc_angle_button = tk.Button(reset_frame, text="Reset Turndisc Angle to 0°", command=Reset_Turndisc_Angle_UI)
reset_turndisc_angle_button.pack(anchor="w", padx=(5, 0), pady = 5)

# Reset Turntable Angle Button
def Reset_Turntable_Angle_UI():
    # Initialize the Antenna Controller (Update the address accordingly)
    AC_Addr = ac_address_entry.get()
    AC = AnCt.Initialize_AC(AC_Addr)
    # Call the Reset_Height function and pass the AC object
    AnCt.Reset_Turntable_Angle(AC)
    # Close the connection to the Antenna Controller
    AC.close()
reset_turntable_angle_button = tk.Button(reset_frame, text="Reset Turntable Angle to 0°", command=Reset_Turntable_Angle_UI)
reset_turntable_angle_button.pack(anchor="w", padx=(5, 0))
###################################################################################################################################
function_check_frame = tk.Frame(ac_frame, bg="#333333")
function_check_frame.pack(side="left", padx=20, pady=20, anchor="sw")
tk.Label(function_check_frame, text="Function Check", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="center")

file_fc_frame = tk.Frame(function_check_frame, bg="#333333")
file_fc_frame.pack()
entry_file = tk.Entry(file_fc_frame, font=("Arial", 12))
entry_file.pack(side=tk.LEFT, padx=5)

def Browse_FC_File():
    FC_File_Name = fd.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xlsm")])
    if FC_File_Name:
        entry_file.delete(0, tk.END)  # Use entry_file here
        entry_file.insert(0, FC_File_Name)
button_browse = tk.Button(file_fc_frame, text="Browse", font=("Arial", 10), command=Browse_FC_File)
button_browse.pack(side=tk.RIGHT, padx=5)
def start_processing_UI():
    # Get the file name from the entry field
    FC_File_Name = entry_file.get()
    FC.start_processing(FC_File_Name)
button_start = tk.Button(function_check_frame, text="Start Function Check", font=("Arial", 10), command=start_processing_UI)
button_start.pack(pady=5)
#########################################################################################################################################
# Receiver Section
rx_frame = tk.Frame(window, bg="#333333")
rx_frame.pack(side="left", padx=20, pady=20, anchor="nw")

tk.Label(rx_frame, text="Receiver", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="center")

rx_address_frame = tk.Frame(rx_frame, bg="#333333")
rx_address_frame.pack(anchor="w")
rx_address_label = tk.Label(rx_address_frame, text="Address:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333")
rx_address_label.pack(anchor="w")
rx_address_entry = tk.Entry(rx_address_frame, width = 50)
rx_address_entry.pack(side="left")
rx_address_entry.insert(0, "USB0::0x2A8D::0x0F0B::MY59050129::0::INSTR")  # Default value
def initialize_receiver():
    Rx_Addr = rx_address_entry.get()
    Rx = Rxr.Initialize_Rx(Rx_Addr)
    # You can perform additional initialization or configuration here
    return Rx
rx_init_button = tk.Button(rx_address_frame, text="Initialize", command=initialize_receiver)
rx_init_button.pack(padx=5)

# # Amplitude Unit Options
# amp_unit_frame = tk.Frame(rx_frame, bg="#333333", pady=10)
# amp_unit_frame.pack(anchor="w")
# tk.Label(amp_unit_frame, text="Amplitude Unit:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
# amp_unit_var = tk.StringVar()
# amp_unit_var.set("dBµV")  # Default value
# tk.Radiobutton(amp_unit_frame, text="dBµV", variable=amp_unit_var, value="dBµV", fg="#FFFFFF", bg="#333333").pack(side="left")
# tk.Radiobutton(amp_unit_frame, text="dBµV/m", variable=amp_unit_var, value="dBµV/m", fg="#FFFFFF", bg="#333333").pack(side="left")
# tk.Radiobutton(amp_unit_frame, text="dBm", variable=amp_unit_var, value="dBm", fg="#FFFFFF", bg="#333333").pack(side="left")
# # Set Button
# set_amplitude_button = tk.Button(rx_frame, text="Set Amplitude")#, command=set_polarization)
# set_amplitude_button.pack(anchor="e", padx=(5, 0))

# Mode Options
mode_frame = tk.Frame(rx_frame, bg="#333333", pady=10)
mode_frame.pack(anchor="w")
tk.Label(mode_frame, text="Measurement Mode:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left", padx=(0, 10))
mode_var = tk.StringVar()
mode_var.set("Spectrum Analyzer")  # Default value
tk.Radiobutton(mode_frame, text="EMI Receiver", variable=mode_var, value="Emi Receiver", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
tk.Radiobutton(mode_frame, text="Spectrum Analyzer", variable=mode_var, value="Spectrum Analyzer", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
def Set_Mode():
    # Initialize the Receiver (Update the address accordingly)
    Rx_Addr = rx_address_entry.get()  # Get the address from the entry field
    Rx = Rxr.Initialize_Rx(Rx_Addr)  # Initializing as QP mode by default
    # Get the selected measurement mode from the UI
    selected_mode = mode_var.get()
    # Set the measurement mode using the new function
    Rxr.Set_Measurement_Mode(Rx, selected_mode)
    # Close the connection to the Receiver
    Rx.close()
# Set Button
set_mode_button = tk.Button(rx_frame, text="Set Mode", command=Set_Mode)
set_mode_button.pack(anchor="e", padx=(5, 0))

# Peak Type Options
peak_type_frame = tk.Frame(rx_frame, bg="#333333", pady=10)
peak_type_frame.pack(anchor="w")
tk.Label(peak_type_frame, text="Peak Measurement Type:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left", padx=(0, 10))
peak_type_var = tk.StringVar()
peak_type_var.set("quasi_peak")  # Default value
tk.Radiobutton(peak_type_frame, text="Quasi Peak", variable=peak_type_var, value="quasi_peak", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
tk.Radiobutton(peak_type_frame, text="Max Peak", variable=peak_type_var, value="max_peak", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
tk.Radiobutton(peak_type_frame, text="Average", variable=peak_type_var, value="average", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
def Handle_Peak_Type_Selection():
    # Initialize the Receiver (Update the address accordingly)
    Rx_Addr = rx_address_entry.get()  # Get the address from the entry field
    Rx = Rxr.Initialize_Rx(Rx_Addr)  # Initializing as QP mode by default
    # Get the selected peak measurement type from the UI
    selected_peak_type = peak_type_var.get()    
    # Initialize traces based on the selected peak type
    if selected_peak_type == "quasi_peak":
        Rxr.Get_Quasi_Peaks(Rx)  # Set trace type for quasi peak measurement
    elif selected_peak_type == "max_peak":
        Rxr.Get_Max_Peaks(Rx)  # Set trace type for max peak measurement
    elif selected_peak_type == "average":
        Rxr.Get_Average_Peaks(Rx)  # Set trace type for average peak measurement
    # Measure peak and plot respective curve
    #Rxr.Get_Peak(Rx)  # Measure and plot based on selected peak type
    # Close the connection to the Receiver
    Rx.close()
# Set Button
set_peak_button = tk.Button(rx_frame, text="Set Peak", command=Handle_Peak_Type_Selection)
set_peak_button.pack(anchor="e", padx=(20, 0))

# Initialize Traces Button
def Initialize_Traces_UI():
    # Initialize the Receiver (Update the address accordingly)
    Rx_Addr = rx_address_entry.get()  # Get the address from the entry field
    Rx = Rxr.Initialize_Rx(Rx_Addr)  # Initializing as QP mode by default
    # Call the Initialize_Traces function from Receiver module
    Rxr.Initialize_Traces(Rx)
    # Close the connection to the Receiver
    Rx.close()
init_traces_button = tk.Button(rx_frame, text="Initialize Traces", width=15, pady=15, command = Initialize_Traces_UI)
init_traces_button.pack(anchor="center")

# # Noise Measurement Trace Options
# noise_trace_frame = tk.Frame(rx_frame, bg="#333333", pady=10)
# noise_trace_frame.pack(anchor="w")
# tk.Label(noise_trace_frame, text="Noise Measurement Trace:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
# noise_trace_var = tk.StringVar()
# noise_trace_var.set("On")  # Default value
# tk.Radiobutton(noise_trace_frame, text="On", variable=noise_trace_var, value="On", fg="#FFFFFF" , bg="#333333").pack(side="left")
# tk.Radiobutton(noise_trace_frame, text="Off", variable=noise_trace_var, value="Off", fg="#FFFFFF", bg="#333333").pack(side="left")
########################################################################################################################################
# Measurement Section
measurement_frame = tk.Frame(window, bg="#333333")
measurement_frame.pack(anchor="center", padx=20, pady=20)
tk.Label(measurement_frame, text="Measurement", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="center")

# Manual Measurement Section
manual_meas_frame = tk.Frame(measurement_frame, bg="#333333")
manual_meas_frame.pack(anchor="w")#, pady=10)
tk.Label(manual_meas_frame, text="Manual Measurement", font=("Arial", 16, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="w")

# Enter Frequency Manually
enter_freq_frame = tk.Frame(manual_meas_frame, bg="#333333")
enter_freq_frame.pack(anchor="w", pady=5)
tk.Label(enter_freq_frame, text="Enter Frequency:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
manual_freq_entry = tk.Entry(enter_freq_frame, width=10)
manual_freq_entry.pack(side="left")
def set_manual_frequency():
    selected_freq = float(manual_freq_entry.get())
    # Initialize the Receiver (Update the address accordingly)
    Rx_Addr = rx_address_entry.get()  # Update with the actual address of the Receiver
    Rx = Rxr.Initialize_Rx(Rx_Addr)
    # Set the manually entered frequency on the receiver
    Rxr.Set_Freq(selected_freq, Rx)
    # Close the connection to the Receiver
    Rx.close()
set_manual_freq_button = tk.Button(enter_freq_frame, text="Set", command=set_manual_frequency)
set_manual_freq_button.pack(side="left", padx=(10, 0))

# Height Scan Button
def perform_height_scan():
    # Call the Ht_Scan_With_Peak function here
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    AC = AnCt.Initialize_AC(AC_Addr)
    Rx = Rxr.Initialize_Rx(Rx_Addr)
    freq = float(manual_freq_entry.get())  # Get the manually entered frequency
    MM.Ht_Scan_With_Peak(AC, Rx, freq)  # Call the Ht_Scan_With_Peak function
    # Close the connections
    AC.close()
    Rx.close()
height_scan_button = tk.Button(manual_meas_frame, text="Height Scan", width=10, command = perform_height_scan)
height_scan_button.pack(side="left")#, padx=(10, 0))#, padx=(20, 0), pady=5)

# Angle Scan Button.
def perform_angle_scan():
    # Call the Ht_Scan_With_Peak function here
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    AC = AnCt.Initialize_AC(AC_Addr)
    Rx = Rxr.Initialize_Rx(Rx_Addr)
    freq = float(manual_freq_entry.get())  # Get the manually entered frequency
    MM.Angle_Scan_With_Peak(AC, Rx, freq)  # Call the Ht_Scan_With_Peak function
    # Close the connections
    AC.close()
    Rx.close()
angle_scan_button = tk.Button(manual_meas_frame, text="Angle Scan", width=10, command = perform_angle_scan)
angle_scan_button.pack(side="left", padx=(20, 0))#, padx=(20, 0))#), pady=5)

# Skip Current Measurement Button
skip_button = tk.Button(manual_meas_frame, text="Skip Current Measurement", width=25)
skip_button.pack(side="left", padx=(20, 0))#, pady=5)

# Automatic Measurement Section
auto_meas_frame = tk.Frame(measurement_frame, bg="#333333")
auto_meas_frame.pack(anchor="w", pady=10)
tk.Label(auto_meas_frame, text="Automatic Measurement", font=("Arial", 16, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="w")

select_file_frame = tk.Frame(auto_meas_frame, bg="#333333")
select_file_frame.pack(anchor="w")#, pady=5)

select_file_entry = tk.Entry(select_file_frame, width=45)
select_file_entry.pack(side="left")

def Browse_File():
    File_Name = fd.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xlsm")])
    if File_Name:
        select_file_entry.delete(0, tk.END)
        select_file_entry.insert(0, File_Name)
        
browse_file_button = tk.Button(select_file_frame, text="Browse Measurement File", width=20, command=Browse_File)
browse_file_button.pack(side="left", padx=(10, 0))

def start_measurement():
    file_name = select_file_entry.get()
    # Read frequencies from the Excel file
    MM.freqs = FDG.Read_From_Excel(file_name)
    MM.Auto_Measure(file_name)
start_button = tk.Button(auto_meas_frame, text="Start Measurement", font="bold", width=20, pady=15, command=start_measurement)
start_button.pack(anchor="center", pady=5)
####################################################################################################################################
# Browse Height Excel File Section
tk.Label(measurement_frame, text="Plot Graphs", font=("Arial", 16, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="w")
height_file_frame = tk.Frame(measurement_frame, bg="#333333")
height_file_frame.pack(anchor="w")#, pady=10)

height_file_entry = tk.Entry(height_file_frame, width=45)
height_file_entry.pack(side="left")

def Browse_Height_File():
    Height_File_Name = fd.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xlsm")])
    if Height_File_Name:
        height_file_entry.delete(0, tk.END)
        height_file_entry.insert(0, Height_File_Name)

browse_height_file_button = tk.Button(height_file_frame, text="Browse Height File", width=15, command=Browse_Height_File)
browse_height_file_button.pack(side="left", padx=(10, 0))

# Plot Height Graph Button
def plot_height_graph():
    height_file_name = height_file_entry.get()
    FDG.plot_height_vs_peak(height_file_name)
plot_height_graph_button = tk.Button(height_file_frame, text="Plot", width=10, command=plot_height_graph)
plot_height_graph_button.pack(side="left", padx=(10, 0))

# Browse Angle Excel File Section
angle_file_frame = tk.Frame(measurement_frame, bg="#333333")
angle_file_frame.pack(anchor="w", pady=10)

angle_file_entry = tk.Entry(angle_file_frame, width=45)
angle_file_entry.pack(side="left")

def Browse_Angle_File():
    Angle_File_Name = fd.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xlsm")])
    if Angle_File_Name:
        angle_file_entry.delete(0, tk.END)
        angle_file_entry.insert(0, Angle_File_Name)

browse_angle_file_button = tk.Button(angle_file_frame, text="Browse Angle File", width=15, command=Browse_Angle_File)
browse_angle_file_button.pack(side="left", padx=(10, 0))

# Plot Angle Graph Button
def plot_angle_graph():
    angle_file_name = angle_file_entry.get()
    FDG.plot_angle_vs_peak_polar(angle_file_name)
plot_angle_graph_button = tk.Button(angle_file_frame, text="Plot", width=10, command=plot_angle_graph)
plot_angle_graph_button.pack(side="left", padx=(10, 0))
#################################################################
# Exit Button
# Place the exit button in the bottom-right corner using grid
exit_button = tk.Button(window, text="Exit", command=window.quit, width=5)
exit_button.pack(side="bottom", anchor="center")  # Use 'sticky' to anchor to the bottom-right (southeast) corner

# Run the GUI main loop
window.mainloop()
