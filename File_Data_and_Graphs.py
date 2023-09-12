#Import necessary libraries
import tkinter as tk
from tkinter import filedialog as fd
#import pyvisa as pv
#import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
#from UI import select_file_entry

# Send command to the device
def Send_Cmd(device, command):
    device.write(command)
# Read response of the device
def Read_Response(device):
    response = device.read()
    return response
#######################################################

# Load file
# def Browse_File():
#     File_Name = fd.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xlsm")])
#     if File_Name:
#         select_file_entry.delete(0, tk.END)
#         select_file_entry.insert(0, File_Name)
# Read file
def Read_From_Excel(File_Name):
    df = pd.read_excel(File_Name)
    Freqs = df.iloc[:, 0].tolist()
    return Freqs
# Write peak values to file
def Write_To_Excel(File_Name, Freqs, Heights, Pk_List_Ht, Angles, Pk_List_Angle, Peak_Values):
    df = pd.read_excel(File_Name)
    df['Peak Values at Height [dBuV]'] = Pk_List_Ht
    df['Respective Height [cm]'] = Heights
    df['Peak Values at Angle [dBuV]'] = Pk_List_Angle
    df['Respective Angle [Degrees]'] = Angles
    df['Peak Value [dBuV]'] = Peak_Values

    df.to_excel(File_Name, index=False)
    
# def save_dict_to_csv(data_dict, file_name):
#     with open(file_name, 'w', newline='') as csvfile:
#         writer = csv.DictWriter(csvfile, fieldnames=data_dict.keys())
#         writer.writeheader()
#         writer.writerows([data_dict])

# def write_ht_dict_to_csv(data_dict, file_name):
#     with open(file_name, 'w', newline='') as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow(['Height (cm)', 'Peak Value (dBuV)'])  # Write header
#         for height, peak_value in data_dict.items():
#             writer.writerow([height, peak_value])

# def write_ang_dict_to_csv(data_dict, file_name):
#     with open(file_name, 'w', newline='') as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow(['Angle (Degrees)', 'Peak Value (dBuV)'])  # Write header
#         for height, peak_value in data_dict.items():
#             writer.writerow([height, peak_value])

def write_ht_dict_to_excel(data_dict, freq, file_name):
    df = pd.DataFrame(data_dict.items(), columns=['Height (cm)', 'Peak Value (dBuV)'])
    sheet_name = f'{freq:.2f} MHz'
    df.to_excel(file_name, sheet_name=sheet_name, index=False)

def write_ang_dict_to_excel(data_dict, freq, file_name):
    df = pd.DataFrame(data_dict.items(), columns=['Angle (Degrees)', 'Peak Value (dBuV)'])
    sheet_name = f'{freq:.2f} MHz'
    df.to_excel(file_name, sheet_name=sheet_name, index=False)
    
def plot_max_peak_vs_freq(freqs, peak_values):
    plt.figure(figsize=(10, 6))
    plt.semilogx(freqs, peak_values)
    #plt.plot(freqs, max_ang_peaks, label='Max Peak at Angle')
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Peak Value (dBuV)')
    plt.title('Peak Value vs Frequency')
    #plt.legend()
    plt.grid()
    plt.show()
#Height (cm)	Peak Value (dBuV)

def plot_height_vs_peak(file_ht_name):
    # Read the data from the Excel file
    data = pd.read_excel(file_ht_name)
    # Filter out negative peak values
    data = data[data.iloc[:, 1] >= 0]  # Column 2 (index 1) corresponds to "Peak" column
    # Extract height and peak values from the filtered data
    heights = data.iloc[:, 0]  # Column 1 (index 0) corresponds to "Height" column
    peaks = data.iloc[:, 1]    # Column 2 (index 1) corresponds to "Peak" column
    plt.plot(peaks, heights, marker='o', linestyle='-')
    plt.xlabel("Peak")
    plt.ylabel("Height")
    plt.title("Height vs. Peak")
    plt.show()

def plot_angle_vs_peak_polar(file_name):
    # Read the data from the Excel file
    data = pd.read_excel(file_name)
    # Extract angle and peak values
    angles = data.iloc[:, 0]  # Assuming column 1 contains angles
    peaks = data.iloc[:, 1]   # Assuming column 2 contains peak values
    # Filter out negative peak values
    positive_peaks = peaks[peaks >= 0]
    # Create a polar plot
    plt.figure(figsize=(6, 6))
    ax = plt.subplot(111, polar=True)
    # Convert angles to radians
    angles_radians = np.radians(angles)
    # Plot peaks at corresponding angles
    ax.plot(angles_radians, positive_peaks, marker='o', linestyle='-', label='Peak Values')
    # Set the polar plot direction clockwise
    ax.set_theta_direction(-1)
    # Set 0 degrees at the top of the plot
    ax.set_theta_offset(np.pi / 2.0)
    # Set labels for the angles
    ax.set_xticks(np.radians(np.arange(0, 360, 45)))
    ax.set_xticklabels(['0°', '45°', '90°', '135°', '180°', '225°', '270°', '315°'])
    # Set the plot title
    plt.title("Angle vs. Peak")
    # Display a legend
    #ax.legend()
    # Show the polar plot
    plt.show()
# Usage example:
# plot_angle_vs_peak_polar("your_angle_vs_peak_data.xlsx")