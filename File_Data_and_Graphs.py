#Import necessary libraries
import tkinter as tk
from tkinter import filedialog as fd
#import pyvisa as pv
#import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.animation as animation
from datetime import datetime
  # Add this import statement

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
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    File_Name = f"{File_Name}_{current_datetime}.xlsx"  # Update the file name
    df.to_excel(File_Name, index=False)

def write_ht_dict_to_excel(data_dict, freq, file_name):
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    df = pd.DataFrame(data_dict.items(), columns=['Height (cm)', 'Peak Value (dBuV)'])
    sheet_name = f'{freq:.2f} MHz_{current_datetime}'
    file_name = f"{file_name}_{current_datetime}.xlsx"  # Update the file name
    df.to_excel(file_name, sheet_name=sheet_name, index=False)

def write_ang_dict_to_excel(data_dict, freq, file_name):
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    df = pd.DataFrame(data_dict.items(), columns=['Angle (Degrees)', 'Peak Value (dBuV)'])
    sheet_name = f'{freq:.2f} MHz_{current_datetime}'
    file_name = f"{file_name}_{current_datetime}.xlsx"  # Update the file name
    df.to_excel(file_name, sheet_name=sheet_name, index=False)

def plot_max_peak_vs_freq(freqs, peak_values):
    plt.figure(figsize=(10, 6))
    plt.semilogx(freqs, peak_values)
    #plt.plot(freqs, max_ang_peaks, label='Max Peak at Angle')
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Peak Value (dBuV/m)')
    plt.title('Peak Value vs Frequency')
    #plt.legend()
    plt.grid()
    plt.show()

# def plot_height_vs_peak_real_time(peak_ht_dict, freq):
#     fig, ax = plt.subplots(figsize=(8, 6))

#     def animate(i):
#         ax.clear()
#         heights, peaks = zip(*sorted(peak_ht_dict.items()))
#         ax.plot(peaks, heights, marker='o', linestyle='-')
#         ax.set_xlabel("Peak Value (dBuV)")
#         ax.set_ylabel("Height (cm)")
#         ax.set_title(f"Height vs. Peak at {freq:.2f} MHz")
#         plt.pause(0.1)

#     ani = animation.FuncAnimation(fig, animate, repeat=False)

#     plt.show()

#Height (cm)	Peak Value (dBuV)

def plot_height_vs_peak(file_ht_name):
    # Read the data from the Excel file
    data = pd.read_excel(file_ht_name)
    # Filter out negative peak values
    data = data[data.iloc[:, 1] >= 0]  # Column 2 (index 1) corresponds to "Peak" column
    # Extract height and peak values from the filtered data
    heights = data.iloc[:, 0]  # Column 1 (index 0) corresponds to "Height" column
    peaks = data.iloc[:, 1]    # Column 2 (index 1) corresponds to "Peak" column

    # Find the maximum peak value and its corresponding height
    max_peak_index = peaks.idxmax()
    max_peak_height = heights[max_peak_index]
    max_peak_value = peaks[max_peak_index]

    # Plot the height vs. peak graph
    plt.figure(figsize=(10, 6))
    plt.plot(peaks, heights, marker='o', linestyle='-')
    plt.scatter(max_peak_value, max_peak_height, color='red', marker='x', label=f'Max Peak: {max_peak_value:.2f} dBuV')
    
    # Label all the peak values with their indexes
    for i, peak in enumerate(peaks):
        plt.annotate(f'{i+1}', (peak, heights.iloc[i]), textcoords="offset points", xytext=(0, 10), ha='center')
    
    plt.xlabel("Peak (dBuV/m)")
    plt.ylabel("Height (cm)")
    plt.title("Height vs. Peak")
    plt.legend()
    plt.show()

def plot_height_vs_peak(file_ht_name):
    # Read the data from the Excel file
    data = pd.read_excel(file_ht_name)
    # Filter out negative peak values
    data = data[data.iloc[:, 1] >= 0]  # Column 2 (index 1) corresponds to "Peak" column
    # Extract height and peak values from the filtered data
    heights = data.iloc[:, 0]  # Column 1 (index 0) corresponds to "Height" column
    peaks = data.iloc[:, 1]    # Column 2 (index 1) corresponds to "Peak" column

    # Find the maximum peak value and its corresponding height
    max_peak_index = peaks.idxmax()
    max_peak_height = heights[max_peak_index]
    max_peak_value = peaks[max_peak_index]

    # Plot the height vs. peak graph
    plt.figure(figsize=(10, 6))
    plt.plot(peaks, heights, marker='o', linestyle='-')
    plt.scatter(max_peak_value, max_peak_height, color='red', marker='o', facecolors='none', edgecolors='red', s=100, label=f'Max Peak: {max_peak_value:.2f} dBuV')
    
    # Label all the peak values with their indexes
    for i, peak in enumerate(peaks):
        plt.annotate(f'{i+1}', (peak, heights.iloc[i]), textcoords="offset points", xytext=(0, 10), ha='center')
    
    plt.xlabel("Peak (dBuV/m)")
    plt.ylabel("Height (cm)")
    plt.title("Height vs. Peak")
    plt.legend()
    plt.show()

def plot_angle_vs_peak_polar(file_name):
    # Read the data from the Excel file
    data = pd.read_excel(file_name)
    # Extract angle and peak values
    angles = data.iloc[:, 0]  # Assuming column 1 contains angles
    peaks = data.iloc[:, 1]   # Assuming column 2 contains peak values
    # Filter out negative peak values
    positive_peaks = peaks[peaks >= 0]

    # Find the maximum peak value and its corresponding angle
    max_peak_index = positive_peaks.idxmax()
    max_peak_angle = angles[max_peak_index]
    max_peak_value = positive_peaks[max_peak_index]

    # Create a polar plot
    plt.figure(figsize=(6, 6))
    ax = plt.subplot(111, polar=True)
    # Convert angles to radians
    angles_radians = np.radians(angles)
    # Plot peaks at corresponding angles
    ax.plot(angles_radians, positive_peaks, marker='o', linestyle='-', label='Peak Values')
    
    # Mark the maximum peak
    ax.scatter(np.radians(max_peak_angle), max_peak_value, color='red', marker='o', facecolors='none', edgecolors='red', s=100, label=f'Max Peak: {max_peak_value:.2f} dBuV')
    
    # Label all the peak values with their indexes
    for i, peak in enumerate(positive_peaks):
        plt.annotate(f'{i+1}', (angles_radians.iloc[i], peak), textcoords="offset points", xytext=(0, 10), ha='center')
    
    # Set the polar plot direction clockwise
    ax.set_theta_direction(-1)
    # Set 0 degrees at the top of the plot
    ax.set_theta_offset(np.pi / 2.0)
    # Set labels for the angles
    ax.set_xticks(np.radians(np.arange(0, 360, 45)))
    ax.set_xticklabels(['0°', '45°', '90°', '135°', '180°', '225°', '270°', '315°'])
    # Set the plot title
    plt.title("Angle vs. Peak")
    plt.legend()
    # Show the polar plot
    plt.show()

# Usage examples:
# plot_height_vs_peak("your_height_vs_peak_data.xlsx")
# plot_angle_vs_peak_polar("your_angle_vs_peak_data.xlsx")
