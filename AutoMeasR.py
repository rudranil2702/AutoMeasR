import pyvisa as pv
import time
import threading
import tkinter as tk
from tkinter import filedialog as fd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
#from scipy.interpolate import interp1d
import matplotlib.animation as animation
from datetime import datetime
import queue
#from matplotlib.animation import FuncAnimation
import matplotlib.gridspec as gridspec
##############################################################################
def Send_Cmd(device, command):
    device.write(command)
# Read response of the device
def Read_Response(device):
    response = device.read()
    return response
##############################################################################
########################    INITIALIZATIONS             ######################
##############################################################################
def Initialize_AC(AC_Addr):
    rm = pv.ResourceManager()
    AC = rm.open_resource(AC_Addr)
    AC.baud_rate = 9600
    AC.data_bits = 8
    AC.parity = pv.constants.Parity.none
    AC.flow_control = pv.constants.VI_ASRL_FLOW_NONE
    AC.read_termination = '\n'
    AC.write_termination = '\n'
    AC.timeout = 20000
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

# def start_polling_thread():
#     polling_thread = threading.Thread(target=start_polling)
#     polling_thread.daemon = True  # Daemonize the thread to exit when the main program exits
#     polling_thread.start()
###############################################################################
#############           MEASUREMENT FUNCTIONS        ##########################
###############################################################################
def Query_Mast_Position(AC):
    current_position = ""
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, "CP")
    response = Read_Response(AC)
    current_position = float(response)
    return current_position

def Set_Freq(Freq, Rx):
    Freq_Hz = Freq * 1e6
    Send_Cmd(Rx, f":FREQ:CENT {Freq_Hz} Hz")
    Send_Cmd(Rx, ":CALC:MARK1 ON")
    Send_Cmd(Rx, ":CALC:MARK1:X 0")
    Send_Cmd(Rx, ":CALC:MARK2:X 0")
    Send_Cmd(Rx, ":CALC:MARK2 ON")
    Send_Cmd(Rx, ":CALC:MARK3:X 0")
    Send_Cmd(Rx, ":CALC:MARK3 ON")

def Read_Quasi_Peaks(Rx):
    Send_Cmd(Rx, ":CALC:MARK2:Y?")
    response = Read_Response(Rx)
    peak = float(response)
    return peak

def Get_Quasi_Peaks(Rx):
    peaks = []
    for _ in range(3):  # Perform marker updates (adjust as needed)
        peak = Read_Quasi_Peaks(Rx)
        peaks.append(peak)
        time.sleep(.05)  # Delay between marker updates (adjust as needed)
    QPk = max(peaks)
    return QPk

def Ht_Scan_With_Peak(AC, Rx, Freq, data_queue):
    data_dict_ht = {}
    p = 0
    Str_Rec = ""
    Set_Freq(Freq, Rx)
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, "CP")
    Str_Rec = Read_Response(AC)
    p = float(Str_Rec)
    if p < 250:
        Send_Cmd(AC, "LD 400 CM NP")
        Send_Cmd(AC, "GO")
        while True:
            current_position = Query_Mast_Position(AC)
            peak_value = Get_Quasi_Peaks(Rx)
            data_dict_ht[current_position] = peak_value
            
            # Update the graph
            data_queue.put((current_position, peak_value))
            
            if current_position >= 389.7:
                break
            time.sleep(0.5)
        return data_dict_ht
    else:
        Send_Cmd(AC, "LD 100 CM NP")
        Send_Cmd(AC, "GO")
        while True:
            current_position = Query_Mast_Position(AC)
            peak_value = Get_Quasi_Peaks(Rx)
            data_dict_ht[current_position] = peak_value
            
            # Update the graph
            data_queue.put((current_position, peak_value))
            
            if current_position <= 100.1:
                break
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

def query_position_TD(AC):
    current_position = ""
    Send_Cmd(AC, "LD DS1 DV")
    Send_Cmd(AC, "CP")
    response = Read_Response(AC)
    current_position = float(response)
    return current_position

def Angle_Scan_With_Peak(AC, Rx, Freq, data_queue):
    data_dict_ang = {}
    p = 0
    Str_Rec = ""
    Set_Freq(Freq, Rx)
    Send_Cmd(AC, "LD DS1 DV")
    Send_Cmd(AC, "CP")
    Str_Rec = Read_Response(AC)
    p = float(Str_Rec)
    if p < 1:
        Send_Cmd(AC, "LD 360 DG NP GO")
        Send_Cmd(AC, "GO")
        while True:
            current_position = query_position_TD(AC)
            peak_value = Get_Quasi_Peaks(Rx)
            data_dict_ang[current_position] = peak_value
            
            # Update the polar graph
# Instead of updating the GUI, push the data to the queue
            data_queue.put((current_position, peak_value))

            
            if current_position >= 359.4:
                break
            time.sleep(0.5)
        return data_dict_ang
    else:
        Send_Cmd(AC, "LD 0 DG NP GO")
        Send_Cmd(AC, "GO")
        while True:
            current_position = query_position_TD(AC)
            peak_value = Get_Quasi_Peaks(Rx)
            data_dict_ang[current_position] = peak_value
            
            # Update the polar graph
# Instead of updating the GUI, push the data to the queue
            data_queue.put((current_position, peak_value))

            
            if current_position <= 0.6:
                break
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
##############################################################################
def Write_To_Excel(File_Name, Freqs, Heights, Pk_List_Ht, Angles, Pk_List_Angle):#, Peak_Values):
    df = pd.read_excel(File_Name)
    df['Respective Height [cm]'] = Heights
    df['Peak Values at Height [dBuV]'] = Pk_List_Ht
    df['Respective Angle [Degrees]'] = Angles
    df['Peak Values at Angle [dBuV]'] = Pk_List_Angle
    #df['Peak Value [dBuV]'] = Peak_Values
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    File_Name = f"{File_Name}_{current_datetime}.xlsx"
    df.to_excel(File_Name, index=False)
    
def write_ht_dict_to_excel(data_dict, freq, file_name):
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    df = pd.DataFrame(data_dict.items(), columns=['Height (cm)', 'Peak Value (dBuV)'])
    sheet_name = f'{freq:.2f} MHz_{current_datetime}'
    file_name = f"{file_name}_{current_datetime}.xlsx"
    df.to_excel(file_name, sheet_name=sheet_name, index=False)
    
def write_ang_dict_to_excel(data_dict, freq, file_name):
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    df = pd.DataFrame(data_dict.items(), columns=['Angle (Degrees)', 'Peak Value (dBuV)'])
    sheet_name = f'{freq:.2f} MHz_{current_datetime}'
    file_name = f"{file_name}_{current_datetime}.xlsx"
    df.to_excel(file_name, sheet_name=sheet_name, index=False)

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

def plot_peak_vs_frequency(freq_list, peak_values):
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=2)
    
    def init():
        line.set_data([], [])
        return line,
    
    def update(num, freq_list, peak_values, line):
        line.set_data(freq_list, peak_values)
        return line,
    
    animation.FuncAnimation(fig, update, len(freq_list), fargs=[freq_list, peak_values, line],
                                  interval=50, blit=True, init_func=init)
    plt.show(block=False)

def plot_height_vs_peak(peak_ht_dict):
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=2)
    
    def init():
        line.set_data([], [])
        return line,
    
    def update(num, peak_ht_dict, line):
        peaks = list(peak_ht_dict.keys())
        heights = list(peak_ht_dict.values())
        line.set_data(peaks, heights)
        return line,
    
    animation.FuncAnimation(fig, update, len(peak_ht_dict), fargs=[peak_ht_dict, line],
                                  interval=50, blit=True, init_func=init)
    plt.show(block=False)

def plot_angle_vs_peak_polar(peak_ang_dict):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='polar')
    line, = ax.plot([], [], lw=2)
    
    def init():
        line.set_data([], [])
        return line,
    
    def update(num, peak_ang_dict, line):
        angles = [float(angle) for angle in peak_ang_dict.keys()]
        peaks = list(peak_ang_dict.values())
        line.set_data(angles, peaks)
        return line,
    
    animation.FuncAnimation(fig, update, len(peak_ang_dict), fargs=[peak_ang_dict, line],
                                  interval=50, blit=True, init_func=init)
    plt.show(block=False)

def threaded_function(func, q, *args, **kwargs):
    """Helper function to run a function in a separate thread and return its result."""
    def wrapper():
        result = func(*args, **kwargs)
        q.put(result)
    thread = threading.Thread(target=wrapper)
    thread.start()
    return thread

plt.ion()

def show_popup():
    messagebox.askyesno("Confirmation", "Press Yes to continue to the next frequency...")

import tkinter.messagebox as messagebox

def confirm_max_point():
    result = messagebox.askyesno("Confirmation", "Is the selected maximum point appropriate?")
    return result

def set_height_and_wait(AC, max_ht_height):
    Send_Cmd(AC, f"LD {max_ht_height} CM NP")
    Send_Cmd(AC, "GO")
    Wait_For_Stop(AC)

xl_max_ht_peak = None
xl_max_ht_height = None
xl_max_ang_peak = None
xl_max_ang_angle = None
def on_click_height(event, ax, peaks_so_far, heights_so_far):
    global prev_red_point, selected_max_ht_peak, selected_max_ht_height
    
    # Check if the click is on the correct axis
    if event.inaxes == ax:
        # Get the coordinates of the click
        x, y = event.xdata, event.ydata
        
        # Find the nearest data point to the click
        dist = [(x - px)**2 + (y - py)**2 for px, py in zip(peaks_so_far, heights_so_far)]
        index = dist.index(min(dist))
        
        # Store the selected maximum point
        selected_max_ht_peak = peaks_so_far[index]
        selected_max_ht_height = heights_so_far[index]
        
        # If there was a previously selected red point, turn it blue
        if prev_red_point:
            ax.plot(prev_red_point[0], prev_red_point[1], 'bo')
        
        # Plot the selected maximum point in red
        ax.plot(selected_max_ht_peak, selected_max_ht_height, 'ro')
        plt.draw()
        
        # Update the previously selected red point
        prev_red_point = (selected_max_ht_peak, selected_max_ht_height)
        global new_max_peak, new_max_height
        new_max_peak = selected_max_ht_peak
        new_max_height = selected_max_ht_height

        
        # Start the set_height_and_wait function in a separate thread
        #threading.Thread(target=set_height_and_wait, args=(AC, max_height)).start()

def on_click_angle(event, ax, peaks_ang_so_far, angles_so_far):
    global prev_red_point_ang, selected_max_ang_peak, selected_max_ang_angle

    # Check if the click is on the correct axis
    # if not event.inaxes:
    #     return
    if event.inaxes == ax:
        # Convert the click event coordinates to display coordinates
        click_x, click_y = event.x, event.y
        # Convert the polar data (angle, peak) coordinates to Cartesian display coordinates
        xy_pixels = ax.transData.transform(np.vstack([angles_so_far, peaks_ang_so_far]).T)
        xpix, ypix = xy_pixels.T
        # Calculate the distance to each point in display coordinates
        distances = np.sqrt((xpix - click_x) ** 2 + (ypix - click_y) ** 2)
        # Identify the index of the nearest point by distance
        nearest_index = np.argmin(distances)
        # Get the data for the selected point
        selected_max_ang_peak = peaks_ang_so_far[nearest_index]
        selected_max_ang_angle = angles_so_far[nearest_index]  # This is in radians
        # If there was a previously selected red point, turn it blue
        if prev_red_point_ang:
            ax.plot(prev_red_point_ang[0], prev_red_point_ang[1], 'bo', markersize=7)  # Make the point a bit larger for visibility
    
        # Plot the selected maximum point in red
        ax.plot(selected_max_ang_angle, selected_max_ang_peak, 'ro', markersize=7)  # Make the point a bit larger for visibility
        plt.draw()
    
        prev_red_point_ang = (selected_max_ang_angle, selected_max_ang_peak)
        global new_max_peak_ang, new_max_angle
        new_max_peak_ang = selected_max_ang_peak
        new_max_angle = selected_max_ang_angle
        
def ask_save_max_points():
    """Display a popup asking the user if they want to save the maximum peaks."""
    result = messagebox.askyesno("Confirmation", "Do you want to save the maximum peaks?")
    return result

def Auto_Measure(file_name, window):
    AC_Addr = 'GPIB1::7::INSTR'
    Rx_Addr = 'USB0::0x2A8D::0x0F0B::MY59050129::0::INSTR'
    Rx = Initialize_Rx(Rx_Addr)
    AC = Initialize_AC(AC_Addr)
    freqs = Read_From_Excel(file_name)

    # Lists to store data for writing to Excel later
    freq_list = []
    max_ht_list = []
    max_ang_list = []
    max_ht_height_list = []
    max_ang_angle_list = []
    heights_so_far = []
    peaks_so_far = []
    angles_so_far = []
    peaks_ang_so_far = []
    freq_list = []
    max_ht_list = []
    max_ang_list = []
    max_ht_height_list = []
    max_ang_angle_list = []

    def reset_and_wait(AC):
        Reset_Height_After_Measurement(AC)
        Wait_For_Stop(AC)
    
    # Create a figure that will contain all three plots
    fig = plt.figure()
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    #fig.state("zoomed")# Adjust the figure size if needed
    # Create a gridspec layout with 2 rows and 2 columns
    gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1])
    # Assign the subplots to the gridspec layout
    #ax1 = fig.add_subplot(gs[0, :])  # Peaks vs Frequency graph (top row, spanning both columns)
    ax2 = fig.add_subplot(gs[:, 0])  # Height vs Peak graph (bottom left)
    fig.canvas.mpl_connect('button_press_event', lambda event: on_click_height(event, ax2, peaks_so_far, heights_so_far))
    ax3 = fig.add_subplot(gs[:, 1], projection='polar')  # Angle vs Peak polar plot (bottom right)
    fig.canvas.mpl_connect('button_press_event', lambda event: on_click_angle(event, ax3, peaks_ang_so_far, angles_so_far))

    # Initial plot for Peak vs Height
    line2, = ax2.plot([], [], lw=2)
    ax2.set_title("Peak vs Height")
    ax2.set_xlabel("Peak Value (dBuV)")
    ax2.set_ylabel("Height (cm)")

    # Initial plot for Angle vs Peak Polar Plot
    line3, = ax3.plot([], [], lw=2)
    ax3.set_title("Angle vs Peak Polar Plot")

    # Perform scans for each frequency
    for freq in freqs:
        global prev_red_point
        prev_red_point = None
        global prev_red_point_ang
        prev_red_point_ang = None
        heights_so_far = []
        peaks_so_far = []
        angles_so_far = []
        peaks_ang_so_far = []
        
        # Clear the axes for height vs. peak and angle vs. peak graphs
        ax2.clear()
        ax3.clear()
        # Reset_Height_After_Measurement(AC)
        # Wait_For_Stop(AC)
        thread2 = threading.Thread(target=reset_and_wait, args=(AC,))
        thread2.start()
        thread2.join()
        
        data_queue_ht = queue.Queue()
        ht_thread = threaded_function(Ht_Scan_With_Peak, data_queue_ht, AC, Rx, freq, data_queue_ht)
        
        # Continuously poll the queue for new data and update the GUI
        while ht_thread.is_alive():
            try:
                current_position, peak_value = data_queue_ht.get(timeout=0.1)
                if peak_value > 10:  # Only plot positive values
                    # Inside the loop where you're plotting for height:
                    heights_so_far.append(current_position)
                    peaks_so_far.append(peak_value)
                    ax2.plot(peaks_so_far, heights_so_far, 'b-')  # 'b-' means blue color, connected line
                    ax2.plot(peak_value, current_position, 'bo')  # 'bo' means blue color, round points
                    ax2.set_title(f"Peak vs Height for {freq} MHz")
                    ax2.set_xlabel("Peak Value (dBuV)")
                    ax2.set_ylabel("Height (cm)")
                    plt.pause(0.1)
            except queue.Empty:
                pass


        window.update_idletasks()  # Update the Tkinter GUI
        window.update()

        ht_thread.join()  # Wait for the thread to finish
        peak_ht_dict = data_queue_ht.get()  # Get the return value from the queue
        
        #max_ht_peak, max_ht_height = find_max_ht_peak(peak_ht_dict)
        #ax2.plot(max_ht_peak, max_ht_height, 'ro')
        # After the height scanning loop:
        max_peak = max(peaks_so_far)
        max_height = heights_so_far[peaks_so_far.index(max_peak)]
        
        # Store the software-selected maximum point as the previous red point
        
        prev_red_point = (max_peak, max_height)
        ax2.plot(max_peak, max_height, 'ro')  # 'ro' means red color, round points
        
        is_max_point_appropriate = confirm_max_point()
        if is_max_point_appropriate:
            xl_max_ht_peak = max_peak
            xl_max_ht_height = max_height
            print(xl_max_ht_peak, xl_max_ht_height)
            set_height_and_wait(AC, max_height)
        if not is_max_point_appropriate:
            messagebox.showinfo("Info", "Please click on the graph to select the appropriate maximum point.")
            plt.waitforbuttonpress()
            # Use the selected maximum point for further processing
            xl_max_ht_peak = new_max_peak
            xl_max_ht_height = new_max_height
            print(xl_max_ht_peak, xl_max_ht_height)
            set_height_and_wait(AC, new_max_height)
        
        q_write_ht = queue.Queue()
        threaded_function(write_ht_dict_to_excel, q_write_ht, peak_ht_dict, freq, f'peak_ht_data_{freq:.2f}MHz.xlsx')
        q_write_ht.get()  # Retrieve any return value or exceptions
        
        data_queue_ang = queue.Queue()
        ang_thread = threaded_function(Angle_Scan_With_Peak, data_queue_ang, AC, Rx, freq, data_queue_ang)
        # Continuously poll the queue for new data and update the GUI
        while ang_thread.is_alive():
            try:
                current_position, peak_value = data_queue_ang.get(timeout=0.1)
                if peak_value > 0:  # Only plot positive values
                    # Inside the loop where you're plotting for angle:
                    angles_so_far.append(np.radians(current_position))
                    peaks_ang_so_far.append(peak_value)
                    ax3.plot(angles_so_far, peaks_ang_so_far, 'b-')
                    ax3.plot(np.radians(current_position), peak_value, 'bo')
                    ax3.set_title(f"Angle vs Peak Polar Plot for {freq} MHz")
                    #ax3.set_rticks(np.arange(20, 70, 5))  # Assuming max_value is the maximum dB value you expect
                    plt.pause(0.1)
            except queue.Empty:
                pass

            window.update_idletasks()  # Update the Tkinter GUI
            window.update()

        ang_thread.join()
        peak_ang_dict = data_queue_ang.get()
        
        #max_ang_peak, max_ang_angle = find_max_ang_peak(peak_ang_dict)
        #ax3.plot(np.radians(max_ang_peak), max_ang_angle, 'ro')
        # After the angle scanning loop:
        max_peak_ang = max(peaks_ang_so_far)
        max_angle = angles_so_far[peaks_ang_so_far.index(max_peak_ang)] #radians
        
        prev_red_point_ang = (max_angle, max_peak_ang)
        ax3.plot(max_angle, max_peak_ang, 'ro')  # Plot the red point for each frequency
        
        is_max_point_appropriate = confirm_max_point()
        if is_max_point_appropriate:
            xl_max_ang_peak = max_peak_ang
            xl_max_ang_angle = np.degrees(max_angle)
            print(xl_max_ang_angle, xl_max_ang_peak)
        if not is_max_point_appropriate:
            messagebox.showinfo("Info", "Please click on the graph to select the appropriate maximum point.")
            plt.waitforbuttonpress()
            xl_max_ang_peak = new_max_peak_ang
            xl_max_ang_angle = np.degrees(new_max_angle)
            print(xl_max_ang_peak, xl_max_ang_angle)
            
        q_write_ang = queue.Queue()
        threaded_function(write_ang_dict_to_excel, q_write_ang, peak_ang_dict, freq, f'peak_ang_data_{freq:.2f}MHz.xlsx')
        q_write_ang.get()  # Retrieve any return value or exceptions
        
        # if prev_red_point:
        #     max_ht_peak, max_ht_height = prev_red_point
        # else:
        #     max_ht_peak = selected_max_ht_peak
        #     max_ht_height = selected_max_ht_height
        
        # if prev_red_point:
        #     max_ang_peak, max_ang_angle = prev_red_point
        # else:
        #     max_ang_peak = selected_max_ang_peak
        #     max_ang_angle = selected_max_ang_angle

        #if ask_save_max_points():
        freq_list.append(freq)
        max_ht_height_list.append(xl_max_ht_height)
        max_ht_list.append(xl_max_ht_peak)
        max_ang_angle_list.append(xl_max_ang_angle) # Convert from radians to degrees
        max_ang_list.append(xl_max_ang_peak)

        show_popup()

    # After all iterations, write the lists to the Excel file
    Write_To_Excel(file_name, freq_list, max_ht_height_list, max_ht_list, max_ang_angle_list, max_ang_list)
    plt.show()

    AC.close()
    Rx.close()
##############################################################################
###################           UI FUNCTIONS           #########################
##############################################################################
window = tk.Tk()
window.title("Radiated Emissions Measurement Software")
window.geometry("1280x720")
window.configure(bg="#333333")
window.state('zoomed')

# Antenna Controller Section
ac_frame = tk.Frame(window, bg="#333333")
ac_frame.pack(side="left", padx=20, pady=20, anchor="nw")

tk.Label(ac_frame, text="Antenna Controller", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="center")

ac_address_frame = tk.Frame(ac_frame, bg="#333333")
ac_address_frame.pack(anchor="w")
tk.Label(ac_address_frame, text="Address:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
ac_address_entry = tk.Entry(ac_address_frame)
ac_address_entry.pack(side="left")
ac_address_entry.insert(0, "GPIB1::7::INSTR")
def initialize_antenna_controller():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    return AC
ac_init_button = tk.Button(ac_address_frame, text="Initialize", command=initialize_antenna_controller)
ac_init_button.pack(padx=(5, 0))
########################Polarization Options##################################
polarization_frame = tk.Frame(ac_frame, bg="#333333", pady=10)
polarization_frame.pack(anchor="w")
tk.Label(polarization_frame, text="Polarization:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left", padx=(0, 10))
polarization_var = tk.StringVar()
polarization_var.set("horizontal")  # Default value
tk.Radiobutton(polarization_frame, text="Vertical", variable=polarization_var, value="vertical", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
tk.Radiobutton(polarization_frame, text="Horizontal", variable=polarization_var, value="horizontal", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
def Set_Polarization():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    selected_polarization = polarization_var.get()
    Send_Cmd(AC, "LD TMPM1 DV")
    if selected_polarization == "vertical":
        Send_Cmd(AC, "PV")
    else:
        Send_Cmd(AC, "PH")
    # Close the connection to the Antenna Controller
    AC.close()
# Set Button
set_polarization_button = tk.Button(ac_frame, text="Set Polarization", command=Set_Polarization)
set_polarization_button.pack(anchor="e", padx=(5, 0))
#######################Distance of Test Options###############################
distance_frame = tk.Frame(ac_frame, bg="#333333", pady=10)
distance_frame.pack(anchor="w")
tk.Label(distance_frame, text="Distance of Test:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left", padx=(0, 10))
distance_var = tk.StringVar()
distance_var.set("3m")  # Default value
tk.Radiobutton(distance_frame, text="3m (Turndisc)", variable=distance_var, value="3m", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
tk.Radiobutton(distance_frame, text="10m (Turntable)", variable=distance_var, value="10m", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
def Set_Distance():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    selected_distance = distance_var.get()
    Send_Cmd(AC, "LD TMPM1 DV")
    if selected_distance == "3m":
        Send_Cmd(AC, "LD 300 CM DYMD")
        Send_Cmd(AC, "LD DS1 DV")
    else:
        Send_Cmd(AC, "LD 1000 CM DYMD")
        Send_Cmd(AC, "LD DT1 DV")
    AC.close()
set_distance_button = tk.Button(ac_frame, text="Set Distance", command=Set_Distance)
set_distance_button.pack(anchor="e", padx=(5, 0))

height_go_frame = tk.Frame(ac_frame, bg="#333333", pady=10)
height_go_frame.pack(anchor="w")
height_label = tk.Label(height_go_frame, text="Height (meters):", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
height_entry = tk.Entry(height_go_frame)
height_entry.pack(side="left")
def go_to_height():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    height = float(height_entry.get())
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, f"LD {height} CM NP")
    Send_Cmd(AC, "GO")
go_height_button = tk.Button(height_go_frame, text="Go", command=go_to_height)
go_height_button.pack(padx=(5, 0))

# Create a label and entry for entering the angle
angle_go_frame = tk.Frame(ac_frame, bg="#333333")
angle_go_frame.pack(anchor="w")
angle_label = tk.Label(angle_go_frame, text="Angle (degrees):", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
angle_entry = tk.Entry(angle_go_frame)
angle_entry.pack(side="left")
def go_to_angle():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    angle = float(angle_entry.get())
    Send_Cmd(AC, "LD DT1 DV")
    Send_Cmd(AC, f"LD {angle} DG NP GO")
go_angle_button = tk.Button(angle_go_frame, text="Go", command=go_to_angle)
go_angle_button.pack(padx=(5, 0))
####################RESET HEIGHT AND ANGLE####################################
reset_frame = tk.Frame(ac_frame, bg="#333333", pady=10)
reset_frame.pack(anchor="w")
def Reset_Height_UI():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, "LD 100 CM NP")
    Send_Cmd(AC, "GO")
    AC.close()
reset_height_button = tk.Button(reset_frame, text="Reset Height to 1m", command=Reset_Height_UI)
reset_height_button.pack(anchor="w", padx=(5, 0), pady=5)
# Reset Turndisc Angle
def Reset_Turndisc_Angle_UI():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    Send_Cmd(AC, "LD DS1 DV")
    Send_Cmd(AC, "LD 0 DG NP GO")
    AC.close()
reset_turndisc_angle_button = tk.Button(reset_frame, text="Reset Turndisc Angle to 0°", command=Reset_Turndisc_Angle_UI)
reset_turndisc_angle_button.pack(anchor="w", padx=(5, 0), pady = 5)
# Reset Turntable Angle
def Reset_Turntable_Angle_UI():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    Send_Cmd(AC, "LD DT1 DV")
    Send_Cmd(AC, "LD 0 DG NP GO")
    AC.close()
reset_turntable_angle_button = tk.Button(reset_frame, text="Reset Turntable Angle to 0°", command=Reset_Turntable_Angle_UI)
reset_turntable_angle_button.pack(anchor="w", padx=(5, 0))
###################################################################################################################################
# function_check_frame = tk.Frame(ac_frame, bg="#333333")
# function_check_frame.pack(side="left", padx=20, pady=20, anchor="sw")
# tk.Label(function_check_frame, text="Function Check", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="center")

# file_fc_frame = tk.Frame(function_check_frame, bg="#333333")
# file_fc_frame.pack()
# entry_file = tk.Entry(file_fc_frame, font=("Arial", 12))
# entry_file.pack(side=tk.LEFT, padx=5)

# def Browse_FC_File():
#     FC_File_Name = fd.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xlsm")])
#     if FC_File_Name:
#         entry_file.delete(0, tk.END)  # Use entry_file here
#         entry_file.insert(0, FC_File_Name)
# button_browse = tk.Button(file_fc_frame, text="Browse", font=("Arial", 10), command=Browse_FC_File)
# button_browse.pack(side=tk.RIGHT, padx=5)
# def start_processing_UI():
#     # Get the file name from the entry field
#     FC_File_Name = entry_file.get()
#     FC.start_processing(FC_File_Name)
# button_start = tk.Button(function_check_frame, text="Start Function Check", font=("Arial", 10), command=start_processing_UI)
# button_start.pack(pady=5)
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
rx_address_entry.insert(0, "USB0::0x2A8D::0x0F0B::MY59050129::0::INSTR")
def initialize_receiver():
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx(Rx_Addr)
    return Rx
rx_init_button = tk.Button(rx_address_frame, text="Initialize", command=initialize_receiver)
rx_init_button.pack(padx=5)
###########################MODE###############################################
mode_frame = tk.Frame(rx_frame, bg="#333333", pady=10)
mode_frame.pack(anchor="w")
tk.Label(mode_frame, text="Measurement Mode:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left", padx=(0, 10))
mode_var = tk.StringVar()
mode_var.set("Spectrum Analyzer")  # Default value
tk.Radiobutton(mode_frame, text="EMI Receiver", variable=mode_var, value="Emi Receiver", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
tk.Radiobutton(mode_frame, text="Spectrum Analyzer", variable=mode_var, value="Spectrum Analyzer", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
def Set_Mode():
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx(Rx_Addr)
    selected_mode = mode_var.get()
    if selected_mode == "Emi Receiver":
        Send_Cmd(Rx, ":INST:SEL EMI")
    else:
        Send_Cmd(Rx, ":INST:SEL SA")
    Rx.close()
# Set Button
set_mode_button = tk.Button(rx_frame, text="Set Mode", command=Set_Mode)
set_mode_button.pack(anchor="e", padx=(5, 0))
#################################Peak Types####################################
# Get max peak values
def Get_Max_Peaks(Rx):
    Send_Cmd(Rx, ":CALC:MARK1:MAX")
    Send_Cmd(Rx, ":CALC:MARK1:Y?")
    response = Read_Response(Rx)
    Pk = float(response)
    return Pk
# Get average peak values
def Get_Average_Peaks(Rx):
    Send_Cmd(Rx, "MARK2:TRAC3:TYPE AVER")
    Send_Cmd(Rx, ":CALC:MAM:DET AVER")
    Send_Cmd(Rx, ":CALC:MARK3:Y?")
    response = Read_Response(Rx)
    Avg = float(response)
    return Avg
peak_type_frame = tk.Frame(rx_frame, bg="#333333", pady=10)
peak_type_frame.pack(anchor="w")
tk.Label(peak_type_frame, text="Peak Measurement Type:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left", padx=(0, 10))
peak_type_var = tk.StringVar()
peak_type_var.set("quasi_peak")
tk.Radiobutton(peak_type_frame, text="Quasi Peak", variable=peak_type_var, value="quasi_peak", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
tk.Radiobutton(peak_type_frame, text="Max Peak", variable=peak_type_var, value="max_peak", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
tk.Radiobutton(peak_type_frame, text="Average", variable=peak_type_var, value="average", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
def Handle_Peak_Type_Selection():
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx(Rx_Addr)
    selected_peak_type = peak_type_var.get()    
    if selected_peak_type == "quasi_peak":
        Get_Quasi_Peaks(Rx)
    elif selected_peak_type == "max_peak":
        Get_Max_Peaks(Rx)
    elif selected_peak_type == "average":
        Get_Average_Peaks(Rx)
    Rx.close()
set_peak_button = tk.Button(rx_frame, text="Set Peak", command=Handle_Peak_Type_Selection)
set_peak_button.pack(anchor="e", padx=(20, 0))
####################         INITIALIZE TRACES        ########################
def Initialize_Traces(Rx):
    Send_Cmd(Rx, ":INIT:CONT ON")
    Send_Cmd(Rx, "TRAC1:TYPE WRIT")
def Initialize_Traces_UI():
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx(Rx_Addr)
    Initialize_Traces(Rx)
    Rx.close()
init_traces_button = tk.Button(rx_frame, text="Initialize Traces", width=15, pady=15, command = Initialize_Traces_UI)
init_traces_button.pack(anchor="center")
##############################################################################
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
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx(Rx_Addr)
    Set_Freq(selected_freq, Rx)
    Rx.close()
set_manual_freq_button = tk.Button(enter_freq_frame, text="Set", command=set_manual_frequency)
set_manual_freq_button.pack(side="left", padx=(10, 0))

# Height Scan Button
def perform_height_scan():
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    Rx = Initialize_Rx(Rx_Addr)
    freq = float(manual_freq_entry.get())
    Ht_Scan_With_Peak(AC, Rx, freq)
    AC.close()
    Rx.close()
height_scan_button = tk.Button(manual_meas_frame, text="Height Scan", width=10, command = perform_height_scan)
height_scan_button.pack(side="left")

# Angle Scan Button.
def perform_angle_scan():
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    Rx = Initialize_Rx(Rx_Addr)
    freq = float(manual_freq_entry.get())
    Angle_Scan_With_Peak(AC, Rx, freq)
    AC.close()
    Rx.close()
angle_scan_button = tk.Button(manual_meas_frame, text="Angle Scan", width=10, command = perform_angle_scan)
angle_scan_button.pack(side="left", padx=(20, 0))

# Skip Current Measurement Button
skip_button = tk.Button(manual_meas_frame, text="Skip Current Measurement", width=25)
skip_button.pack(side="left", padx=(20, 0))

# Automatic Measurement Section
auto_meas_frame = tk.Frame(measurement_frame, bg="#333333")
auto_meas_frame.pack(anchor="w", pady=10)
tk.Label(auto_meas_frame, text="Automatic Measurement", font=("Arial", 16, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="w")

select_file_frame = tk.Frame(auto_meas_frame, bg="#333333")
select_file_frame.pack(anchor="w")

select_file_entry = tk.Entry(select_file_frame, width=45)
select_file_entry.pack(side="left")

def Browse_File():
    File_Name = fd.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xlsm")])
    if File_Name:
        select_file_entry.delete(0, tk.END)
        select_file_entry.insert(0, File_Name)
        
browse_file_button = tk.Button(select_file_frame, text="Browse Measurement File", width=20, command=Browse_File)
browse_file_button.pack(side="left", padx=(10, 0))

def Read_From_Excel(File_Name):
    df = pd.read_excel(File_Name)
    Freqs = df.iloc[:, 0].tolist()
    return Freqs

def start_measurement(window):
    file_name = select_file_entry.get()
    # Read frequencies from the Excel file
    Read_From_Excel(file_name)
    Auto_Measure(file_name, window)

start_button = tk.Button(auto_meas_frame, text="Start Measurement", command=lambda: start_measurement(window))
start_button.pack()
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
    plot_height_vs_peak(height_file_name)
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
    plot_angle_vs_peak_polar(angle_file_name)
plot_angle_graph_button = tk.Button(angle_file_frame, text="Plot", width=10, command=plot_angle_graph)
plot_angle_graph_button.pack(side="left", padx=(10, 0))
#################################################################
# Exit Button
exit_button = tk.Button(window, text="Exit", command=window.quit, width=5)
exit_button.pack(side="bottom", anchor="center")
# Run the GUI main loop
window.mainloop()