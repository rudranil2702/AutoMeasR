##################       IMPORT STATEMENTS (write comments)      #############
import pyvisa as pv
import time
import threading
import tkinter as tk
from tkinter import filedialog as fd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation
from datetime import datetime
import queue
import tkinter.messagebox as messagebox
import matplotlib.gridspec as gridspec
##############                   COMMANDS                   ###################
def Send_Cmd(Device, Command): # Send Command to the Device
    Device.write(Command)
def Read_Response(Device): # Read Device Response
    Response = Device.read()
    return Response
##############################################################################
########################    INITIALIZATIONS             ######################
##############################################################################
def Initialize_AC(AC_Addr): # Initialize Antenna Controller
    rm = pv.ResourceManager()
    AC = rm.open_resource(AC_Addr)
    Send_Cmd(AC, "LD 1 INT AP")
    AC.baud_rate = 9600
    AC.data_bits = 8
    AC.parity = pv.constants.Parity.none
    AC.flow_control = pv.constants.VI_ASRL_FLOW_NONE
    AC.read_termination = '\n'
    AC.write_termination = '\n'
    AC.timeout = 20000
    return AC

def Initialize_Rx(Rx_Addr): # Initialize Receiver
    rm = pv.ResourceManager()
    Rx = rm.open_resource(Rx_Addr)
    return Rx

def Initialize_Rx_Auto(Rx_Addr): # Initialize Receiver for Automatic Measurement
    rm = pv.ResourceManager()
    Rx = rm.open_resource(Rx_Addr)
    Set_Receiver_State()
    return Rx
###############################################################################
#############           MEASUREMENT FUNCTIONS        ##########################
###############################################################################
def Query_Mast_Position(AC): # Returns the Current Position of Antenna Mast
    current_position = ""
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, "CP")
    response = Read_Response(AC)
    current_position = float(response)
    return current_position

def Set_Freq(Freq, Rx): # Sets Frequency on the Receiver
    Freq_Hz = Freq * 1e6
    Send_Cmd(Rx, f":FREQ:CENT {Freq_Hz} Hz")
    Send_Cmd(Rx, ":CALC:MARK1 ON")
    Send_Cmd(Rx, ":CALC:MARK1:X 0")
    Send_Cmd(Rx, ":CALC:MARK2:X 0")
    Send_Cmd(Rx, ":CALC:MARK2 ON")
    Send_Cmd(Rx, ":CALC:MARK3:X 0")
    Send_Cmd(Rx, ":CALC:MARK3 ON")

def Read_Quasi_Peaks(Rx): # Reads Quasi Peak Amplitude from the Receiver
    Send_Cmd(Rx, ":CALC:MARK2:Y?")
    response = Read_Response(Rx)
    peak = float(response)
    return peak

def Get_Quasi_Peaks(Rx): # Continuously polls Quasi Peak Amplitude
    peaks = []
    for _ in range(3):
        peak = Read_Quasi_Peaks(Rx)
        peaks.append(peak)
        time.sleep(.05)
    QPk = max(peaks)
    return QPk

def Height_Scan_With_Peak(AC, Rx, Freq, data_queue): # Height Scan returning respective Height and Peak values
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
            data_queue.put((current_position, peak_value))
            if current_position <= 100.1:
                break
            time.sleep(0.5)
        return data_dict_ht

def Find_Max_Height_Peak(data_dict_ht):
    if not data_dict_ht:
        return None, None
    max_peak_value = -float('inf')
    max_peak_height = None
    for height, peak_value in data_dict_ht.items():
        if peak_value > max_peak_value:
            max_peak_value = peak_value
            max_peak_height = height
    return max_peak_value, max_peak_height

def Query_Position_Turndisc(AC): # Returns the Current Position of Turndisc
    current_position = ""
    Send_Cmd(AC, "LD DS1 DV")
    Send_Cmd(AC, "CP")
    response = Read_Response(AC)
    current_position = float(response)
    return current_position

def Query_Position_Turntable(AC): # Returns the Current Position of Turntable
    current_position = ""
    Send_Cmd(AC, "LD DT1 DV")
    Send_Cmd(AC, "CP")
    response = Read_Response(AC)
    current_position = float(response)
    return current_position

def Angle_Scan_With_Peak_Turndisc(AC, Rx, Freq, data_queue): # Angle Scan returning respective Angle and Peak values for Turndisc
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
            current_position = Query_Position_Turndisc(AC)
            peak_value = Get_Quasi_Peaks(Rx)
            data_dict_ang[current_position] = peak_value
            data_queue.put((current_position, peak_value))
            if current_position >= 359.4:
                break
            time.sleep(0.5)
        return data_dict_ang
    else:
        Send_Cmd(AC, "LD 0 DG NP GO")
        Send_Cmd(AC, "GO")
        while True:
            current_position = Query_Position_Turndisc(AC)
            peak_value = Get_Quasi_Peaks(Rx)
            data_dict_ang[current_position] = peak_value
            data_queue.put((current_position, peak_value))
            if current_position <= 0.6:
                break
            time.sleep(0.5)
        return data_dict_ang

def Angle_Scan_With_Peak_Turntable(AC, Rx, Freq, data_queue_tt): # Angle Scan returning respective Angle and Peak values for Turntables
    Set_Turntable(AC)
    data_dict_ang_tt = {}
    p = 0
    Str_Rec = ""
    Set_Freq(Freq, Rx)
    Send_Cmd(AC, "LD DT1 DV")
    Send_Cmd(AC, "CP")
    Str_Rec = Read_Response(AC)
    p = float(Str_Rec)
    if p < 1:
        Send_Cmd(AC, "LD 360 DG NP GO")
        Send_Cmd(AC, "GO")
        while True:
            current_position = Query_Position_Turntable(AC)
            peak_value = Get_Quasi_Peaks(Rx)
            data_dict_ang_tt[current_position] = peak_value
            data_queue_tt.put((current_position, peak_value))
            if current_position >= 359.4:
                break
            time.sleep(0.5)
        return data_dict_ang_tt
    else:
        Send_Cmd(AC, "LD 0 DG NP GO")
        Send_Cmd(AC, "GO")
        while True:
            current_position = Query_Position_Turntable(AC)
            peak_value = Get_Quasi_Peaks(Rx)
            data_dict_ang_tt[current_position] = peak_value
            data_queue_tt.put((current_position, peak_value))
            if current_position <= 0.6:
                break
            time.sleep(0.5)
        return data_dict_ang_tt

def Find_Max_Angle_Peak(data_dict_ang):
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
def Read_From_Excel(file_name):
    df = pd.read_excel(file_name, usecols=[0, 1, 2, 3])
    frequencies = df.iloc[:, 0].tolist()
    sac_angles = df.iloc[:, 1].tolist()
    polarizations = df.iloc[:, 2].tolist()
    limits = df.iloc[:, 3].tolist()
    measurement_parameters = list(zip(frequencies, sac_angles, polarizations, limits))
    return measurement_parameters

def Write_To_Excel(File_Name, Freqs, Heights, Pk_List_Ht, Angles, Pk_List_Angle, Final_Peak_List, Deviations_List):
    df = pd.read_excel(File_Name)
    
    # Error correction for mismatched lengths
    def correct_length(data):
        if len(data) != len(df):
            data += ["No Data Found"] * (len(df) - len(data))
        return data

    df['Respective Height [cm]'] = correct_length(Heights)
    df['Quasi Peak Values at Height [dBµV/m]'] = correct_length(Pk_List_Ht)
    df['Respective Angle [Degrees]'] = correct_length(Angles)
    df['Quasi Peak Values at Angle [dBµV/m]'] = correct_length(Pk_List_Angle)
    df['Final Quasi Peak (dBµV/m)'] = correct_length(Final_Peak_List)
    df['Quasi Peak Deviations (dBµV/m)'] = correct_length(Deviations_List)

    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    File_Name = f"{File_Name}_{current_datetime}.xlsx"
    df.to_excel(File_Name, index=False)
    
def Write_Height_Dictionary_To_Excel(data_dict, freq, file_name):
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    df = pd.DataFrame(data_dict.items(), columns=['Height (cm)', 'Quasi Peak Value (dBµV/m)'])
    sheet_name = f'{freq:.2f} MHz_{current_datetime}'
    file_name = f"{file_name}_{current_datetime}.xlsx"
    df.to_excel(file_name, sheet_name=sheet_name, index=False)
    
def Write_Angle_Dictionary_To_Excel(data_dict, freq, file_name):
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    df = pd.DataFrame(data_dict.items(), columns=['Angle (Degrees)', 'Quasi Peak Value (dBµV/m)'])
    sheet_name = f'{freq:.2f} MHz_{current_datetime}'
    file_name = f"{file_name}_{current_datetime}.xlsx"
    df.to_excel(file_name, sheet_name=sheet_name, index=False)

Sim_Flag = False
Verbose = False
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

def Reset_Height_After_Measurement(AC): # Resets Height After Measurement
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

def Plot_Peak_vs_Frequency(freq_list, peak_values): # Plots Peak vs Frequency Graph
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

def Plot_Height_vs_Peak(peak_ht_dict): # Plots Height vs Peak Graph
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

def Plot_Angle_vs_Peak_Polar(peak_ang_dict): # Plots Angle vs Peak Graph
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

def Threaded_Function(func, q, *args, **kwargs): # Implements Multithreading
    def Wrapper():
        result = func(*args, **kwargs)
        q.put(result)
    thread = threading.Thread(target=Wrapper)
    thread.start()
    return thread

plt.ion() # Turns on interactive Graph

def Show_Popup(): # Shows Next Iteration Popup
    messagebox.showinfo("Confirmation", "Press Okay to go to the next frequency.")
    
def Confirm_Maximum_Point(): # Shows Confirmation for maximum point Popup
    result = messagebox.askyesno("Confirmation", "Is the selected maximum point appropriate?")
    return result

def Set_Height_And_Wait(AC, max_ht_height): # Sets Height at which Max Peak Found
    Send_Cmd(AC, f"LD {max_ht_height} CM NP")
    Send_Cmd(AC, "GO")
    Wait_For_Stop(AC)
    
def Reset_Turndisc(AC): # Resets Turndisc after Measurement
    cp = Query_Position_Turndisc(AC)
    if cp < 180:
        Send_Cmd(AC, "LD DS1 DV")
        Send_Cmd(AC, "LD 0 DG NP GO")
        Wait_For_Stop(AC)
    else:
        Send_Cmd(AC, "LD DS1 DV")
        Send_Cmd(AC, "LD 360 DG NP GO")
        Wait_For_Stop(AC)
        
def Reset_Turntable(AC): # Resets Turntable after Measurement
    cp = Query_Position_Turntable(AC)
    if cp < 180:
        Send_Cmd(AC, "LD DT1 DV")
        Send_Cmd(AC, "LD 0 DG NP GO")
        Wait_For_Stop(AC)
    else:
        Send_Cmd(AC, "LD DT1 DV")
        Send_Cmd(AC, "LD 360 DG NP GO")
        Wait_For_Stop(AC)
    
def Go_To_SAC_Angle_Turndisc(AC, sac): # Sends Turndisc to respective max peak Angle
    Send_Cmd(AC, "LD DS1 DV")
    Send_Cmd(AC, f"LD {sac} DG NP GO")
    Wait_For_Stop(AC)

def Go_To_SAC_Angle_Turntable(AC, sac): # Sends Turntable to respective max peak Angle
    Send_Cmd(AC, "LD DT1 DV")
    Send_Cmd(AC, f"LD {sac} DG NP GO")
    Wait_For_Stop(AC)

v_list = ["vertical","ver","v","VERTICAL","Vertical","Ver","VER","V"]   
h_list = ["horizontal","hor","h","HORIZONTAL","Horizontal","Hor","HOR","H"] 
def Go_To_Polarization(AC, polarization): # Goes to allocated Polarization
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    Send_Cmd(AC, "LD TMPM1 DV")
    if polarization in v_list:
        Send_Cmd(AC, "PV")
    elif polarization in h_list:
        Send_Cmd(AC, "PH")
    Wait_For_Stop(AC)

xl_max_ht_peak = None
xl_max_ht_height = None
xl_max_ang_peak = None
xl_max_ang_angle = None
def On_Click_Height(event, ax, peaks_so_far, heights_so_far): # Reads and updates user selected point on graph for Height Scan
    global prev_red_point, selected_max_ht_peak, selected_max_ht_height
    if event.inaxes == ax:
        x, y = event.xdata, event.ydata
        dist = [(x - px)**2 + (y - py)**2 for px, py in zip(peaks_so_far, heights_so_far)]
        index = dist.index(min(dist))
        selected_max_ht_peak = peaks_so_far[index]
        selected_max_ht_height = heights_so_far[index]
        if prev_red_point:
            ax.plot(prev_red_point[0], prev_red_point[1], 'bo')
        ax.plot(selected_max_ht_peak, selected_max_ht_height, 'ro')
        plt.draw()
        prev_red_point = (selected_max_ht_peak, selected_max_ht_height)
        global new_max_peak, new_max_height
        new_max_peak = selected_max_ht_peak
        new_max_height = selected_max_ht_height

def On_Click_Angle(event, ax, peaks_ang_so_far, angles_so_far): # Reads and updates user selected point on graph for Angle Scan
    global prev_red_point_ang, selected_max_ang_peak, selected_max_ang_angle
    if event.inaxes == ax:
        click_x, click_y = event.x, event.y
        xy_pixels = ax.transData.transform(np.vstack([angles_so_far, peaks_ang_so_far]).T)
        xpix, ypix = xy_pixels.T
        distances = np.sqrt((xpix - click_x) ** 2 + (ypix - click_y) ** 2)
        nearest_index = np.argmin(distances)
        selected_max_ang_peak = peaks_ang_so_far[nearest_index]
        selected_max_ang_angle = angles_so_far[nearest_index]
        if prev_red_point_ang:
            ax.plot(prev_red_point_ang[0], prev_red_point_ang[1], 'bo', markersize=7)
        ax.plot(selected_max_ang_angle, selected_max_ang_peak, 'ro', markersize=7)
        plt.draw()
    
        prev_red_point_ang = (selected_max_ang_angle, selected_max_ang_peak)
        global new_max_peak_ang, new_max_angle
        new_max_peak_ang = selected_max_ang_peak
        new_max_angle = selected_max_ang_angle

def Auto_Measure_Turndisc(file_name, window): # Performs Automatic Measurement for Turndisc
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx_Auto(Rx_Addr)
    AC = Initialize_AC(AC_Addr)
    measurement_parameters = Read_From_Excel(file_name)
    window.iconify()
    
    freq_list = []
    max_ht_list = []
    max_ang_list = []
    max_ht_height_list = []
    max_ang_angle_list = []
    heights_so_far = []
    peaks_so_far = []
    angles_so_far = []
    peaks_ang_so_far = []
    max_ht_list = []
    max_ang_list = []
    max_ht_height_list = []
    max_ang_angle_list = []
    final_peak_list = []
    deviations_list = []

    def Reset_And_Wait(AC):
        Reset_Height_After_Measurement(AC)
        #Reset_Angle_After_Measurement_Turndisc(AC)
        Wait_For_Stop(AC)
    
    fig = plt.figure()
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1])
    ax2 = fig.add_subplot(gs[:, 0])
    fig.canvas.mpl_connect('button_press_event', lambda event: On_Click_Height(event, ax2, peaks_so_far, heights_so_far))
    ax3 = fig.add_subplot(gs[:, 1], projection='polar')
    fig.canvas.mpl_connect('button_press_event', lambda event: On_Click_Angle(event, ax3, peaks_ang_so_far, angles_so_far))
    line2, = ax2.plot([], [], lw=2)
    ax2.set_title("Quasi Peak vs Height")
    ax2.set_xlabel("Quasi Peak Value (dBµV/m)")
    ax2.set_ylabel("Antenna Mast Height (cm)")
    line3, = ax3.plot([], [], lw=2)
    ax3.set_title("Angle vs Quasi Peak Polar Plot")
    ax2.grid(True)
    ax3.grid(True)

    # Perform scans for each frequency
    for params in measurement_parameters:
        freq, sac, polarization, limits = params
        global prev_red_point
        prev_red_point = None
        global prev_red_point_ang
        prev_red_point_ang = None
        heights_so_far = []
        peaks_so_far = []
        angles_so_far = []
        peaks_ang_so_far = []
        ax2.clear()
        ax3.clear()
        
        ax2.axvline(x=limits, color='r', linestyle='--') 
        theta = np.linspace(0, 2*np.pi, 100)  # Generate 100 points for a complete circle
        circle_x = limits * np.cos(theta)  # Calculate x coordinates
        circle_y = limits * np.sin(theta)  # Calculate y coordinates
        ax3.plot(theta, np.sqrt(circle_x**2 + circle_y**2), color='r', linestyle='--')  # Draw a circle
        
        thread2 = threading.Thread(target=Reset_And_Wait, args=(AC,))
        thread2.start()
        thread2.join()
        
        Go_To_Polarization(AC, polarization)
        Go_To_SAC_Angle_Turndisc(AC, sac)
        
        data_queue_ht = queue.Queue()
        ht_thread = Threaded_Function(Height_Scan_With_Peak, data_queue_ht, AC, Rx, freq, data_queue_ht)
        while ht_thread.is_alive():
            try:
                current_position, peak_value = data_queue_ht.get(timeout=0.1)
                if peak_value > 0:
                    heights_so_far.append(current_position)
                    peaks_so_far.append(peak_value)
                    ax2.plot(peaks_so_far, heights_so_far, 'b-')
                    ax2.plot(peak_value, current_position, 'bo')
                    ax2.set_title(f"Quasi Peak vs Height for {freq} MHz")
                    ax2.set_xlabel("Quasi Peak Value (dBµV/m)")
                    ax2.set_ylabel("Antenna Mast Height (cm)")
                    plt.pause(0.1)
            except queue.Empty:
                pass
        window.update_idletasks()
        window.update()
        ht_thread.join()
        peak_ht_dict = data_queue_ht.get()

        max_peak = max(peaks_so_far)
        max_height = heights_so_far[peaks_so_far.index(max_peak)]

        prev_red_point = (max_peak, max_height)
        ax2.plot(max_peak, max_height, 'ro')
        
        is_max_point_appropriate = Confirm_Maximum_Point()
        if is_max_point_appropriate:
            xl_max_ht_peak = max_peak
            xl_max_ht_height = max_height
            print(xl_max_ht_peak, xl_max_ht_height)
            Set_Height_And_Wait(AC, max_height)
        if not is_max_point_appropriate:
            messagebox.showinfo("Info", "Please click on the Graph to select the Correct Maximum Point.")
            plt.waitforbuttonpress()
            xl_max_ht_peak = new_max_peak
            xl_max_ht_height = new_max_height
            #print(xl_max_ht_peak, xl_max_ht_height)
            Set_Height_And_Wait(AC, new_max_height)
            
        q_write_ht = queue.Queue()
        Threaded_Function(Write_Height_Dictionary_To_Excel, q_write_ht, peak_ht_dict, freq, f'peak_ht_data_{freq:.2f}MHz.xlsx')
        q_write_ht.get()
        
        Reset_Turndisc(AC)
        
        data_queue_ang = queue.Queue()
        ang_thread = Threaded_Function(Angle_Scan_With_Peak_Turndisc, data_queue_ang, AC, Rx, freq, data_queue_ang)
        while ang_thread.is_alive():
            try:
                current_position, peak_value = data_queue_ang.get(timeout=0.1)
                if peak_value > 0:
                    angles_so_far.append(np.radians(current_position))
                    peaks_ang_so_far.append(peak_value)
                    ax3.plot(angles_so_far, peaks_ang_so_far, 'b-')
                    ax3.plot(np.radians(current_position), peak_value, 'bo')
                    ax3.set_title(f"Angle vs Quasi Peak Polar Plot for {freq} MHz")
                    plt.pause(0.1)
            except queue.Empty:
                pass
            window.update_idletasks()
            window.update()
        ang_thread.join()
        peak_ang_dict = data_queue_ang.get()

        max_peak_ang = max(peaks_ang_so_far)
        max_angle = angles_so_far[peaks_ang_so_far.index(max_peak_ang)]
        
        prev_red_point_ang = (max_angle, max_peak_ang)
        ax3.plot(max_angle, max_peak_ang, 'ro')
        
        is_max_point_appropriate = Confirm_Maximum_Point()
        if is_max_point_appropriate:
            xl_max_ang_peak = max_peak_ang
            xl_max_ang_angle = np.degrees(max_angle)
            #print(xl_max_ang_angle, xl_max_ang_peak)
        if not is_max_point_appropriate:
            messagebox.showinfo("Info", "Please click on the Graph to select the correct Maximum Point.")
            plt.waitforbuttonpress()
            xl_max_ang_peak = new_max_peak_ang
            xl_max_ang_angle = np.degrees(new_max_angle)
            #print(xl_max_ang_peak, xl_max_ang_angle)
            
        q_write_ang = queue.Queue()
        Threaded_Function(Write_Angle_Dictionary_To_Excel, q_write_ang, peak_ang_dict, freq, f'peak_ang_data_{freq:.2f}MHz.xlsx')
        q_write_ang.get()
        
        if xl_max_ht_peak >= xl_max_ang_peak:
            final_peak_list.append(xl_max_ht_peak)
            deviation = limits - xl_max_ht_peak
            deviations_list.append(deviation)
        else:
            final_peak_list.append(xl_max_ang_peak)
            deviation = limits - xl_max_ang_peak
            deviations_list.append(deviation)
        
        freq_list.append(freq)
        max_ht_height_list.append(xl_max_ht_height)
        max_ht_list.append(xl_max_ht_peak)
        max_ang_angle_list.append(xl_max_ang_angle)
        max_ang_list.append(xl_max_ang_peak)
        
        Show_Popup()
        
        # user_response = Show_Popup()

        # if not user_response:
        #     # If the user clicks 'No', break the loop
        #     break
    Write_To_Excel(file_name, freq_list, max_ht_height_list, max_ht_list, max_ang_angle_list, max_ang_list, final_peak_list, deviations_list)
    plt.show()

    AC.close()
    Rx.close()
    
def Set_Turntable(AC): # Sets Turntable as Active Device
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, "LD 1000 CM DYMD")
    Send_Cmd(AC, "LD DT1 DV")
    
def Auto_Measure_Turntable(file_name, window): # Performs Automatic Measurement for Turntable
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx_Auto(Rx_Addr)
    AC = Initialize_AC(AC_Addr)
    measurement_parameters = Read_From_Excel(file_name)
    window.iconify()
    
    freq_list = []
    max_ht_list = []
    max_ang_list = []
    max_ht_height_list = []
    max_ang_angle_list = []
    heights_so_far = []
    peaks_so_far = []
    angles_so_far = []
    peaks_ang_so_far = []
    max_ht_list = []
    max_ang_list = []
    max_ht_height_list = []
    max_ang_angle_list = []
    final_peak_list = []
    deviations_list = []

    def Reset_And_Wait(AC):
        Reset_Height_After_Measurement(AC)
        #Reset_Angle_After_Measurement_Turntable(AC)
        Wait_For_Stop(AC)
    
    fig = plt.figure()
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1])
    ax2 = fig.add_subplot(gs[:, 0])
    fig.canvas.mpl_connect('button_press_event', lambda event: On_Click_Height(event, ax2, peaks_so_far, heights_so_far))
    ax3 = fig.add_subplot(gs[:, 1], projection='polar')
    fig.canvas.mpl_connect('button_press_event', lambda event: On_Click_Angle(event, ax3, peaks_ang_so_far, angles_so_far))
    line2, = ax2.plot([], [], lw=2)
    ax2.set_title("Quasi Peak vs Height")
    ax2.set_xlabel("Quasi Peak Value (dBµV/m)")
    ax2.set_ylabel("Antenna Mast Height (cm)")
    line3, = ax3.plot([], [], lw=2)
    ax3.set_title("Angle vs Quasi Peak Polar Plot")
    ax2.grid(True)
    ax3.grid(True)

    # Perform scans for each frequency
    for params in measurement_parameters:
        freq, sac, polarization, limits = params
        global prev_red_point
        prev_red_point = None
        global prev_red_point_ang
        prev_red_point_ang = None
        heights_so_far = []
        peaks_so_far = []
        angles_so_far = []
        peaks_ang_so_far = []
        ax2.clear()
        ax3.clear()
        
        ax2.axvline(x=limits, color='r', linestyle='--') 
        theta = np.linspace(0, 2*np.pi, 100)  # Generate 100 points for a complete circle
        circle_x = limits * np.cos(theta)  # Calculate x coordinates
        circle_y = limits * np.sin(theta)  # Calculate y coordinates
        ax3.plot(theta, np.sqrt(circle_x**2 + circle_y**2), color='r', linestyle='--')  # Draw a circle
        
        thread2 = threading.Thread(target=Reset_And_Wait, args=(AC,))
        thread2.start()
        thread2.join()
        
        Go_To_Polarization(AC, polarization)
        Go_To_SAC_Angle_Turntable(AC, sac)
        
        data_queue_ht = queue.Queue()
        ht_thread = Threaded_Function(Height_Scan_With_Peak, data_queue_ht, AC, Rx, freq, data_queue_ht)
        while ht_thread.is_alive():
            try:
                current_position, peak_value = data_queue_ht.get(timeout=0.1)
                if peak_value > 0:
                    heights_so_far.append(current_position)
                    peaks_so_far.append(peak_value)
                    ax2.plot(peaks_so_far, heights_so_far, 'b-')
                    ax2.plot(peak_value, current_position, 'bo')
                    ax2.set_title(f"Quasi Peak vs Height for {freq} MHz")
                    ax2.set_xlabel("Quasi Peak Value (dBµV/m)")
                    ax2.set_ylabel("Antenna Mast Height (cm)")
                    plt.pause(0.1)
            except queue.Empty:
                pass
        window.update_idletasks()
        window.update()
        ht_thread.join()
        peak_ht_dict = data_queue_ht.get()

        max_peak = max(peaks_so_far)
        max_height = heights_so_far[peaks_so_far.index(max_peak)]

        prev_red_point = (max_peak, max_height)
        ax2.plot(max_peak, max_height, 'ro')
        
        is_max_point_appropriate = Confirm_Maximum_Point()
        if is_max_point_appropriate:
            xl_max_ht_peak = max_peak
            xl_max_ht_height = max_height
            print(xl_max_ht_peak, xl_max_ht_height)
            Set_Height_And_Wait(AC, max_height)
        if not is_max_point_appropriate:
            messagebox.showinfo("Info", "Please click on the Graph to select the Correct Maximum Point.")
            plt.waitforbuttonpress()
            xl_max_ht_peak = new_max_peak
            xl_max_ht_height = new_max_height
            #print(xl_max_ht_peak, xl_max_ht_height)
            Set_Height_And_Wait(AC, new_max_height)
            
        q_write_ht = queue.Queue()
        Threaded_Function(Write_Height_Dictionary_To_Excel, q_write_ht, peak_ht_dict, freq, f'peak_ht_data_{freq:.2f}MHz.xlsx')
        q_write_ht.get()
        
        Reset_Turntable(AC)
        
        data_queue_ang = queue.Queue()
        ang_thread = Threaded_Function(Angle_Scan_With_Peak_Turntable, data_queue_ang, AC, Rx, freq, data_queue_ang)
        while ang_thread.is_alive():
            try:
                current_position, peak_value = data_queue_ang.get(timeout=0.1)
                if peak_value > 0:
                    angles_so_far.append(np.radians(current_position))
                    peaks_ang_so_far.append(peak_value)
                    ax3.plot(angles_so_far, peaks_ang_so_far, 'b-')
                    ax3.plot(np.radians(current_position), peak_value, 'bo')
                    ax3.set_title(f"Angle vs Quasi Peak Polar Plot for {freq} MHz")
                    plt.pause(0.1)
            except queue.Empty:
                pass
            window.update_idletasks()
            window.update()
        ang_thread.join()
        peak_ang_dict = data_queue_ang.get()

        max_peak_ang = max(peaks_ang_so_far)
        max_angle = angles_so_far[peaks_ang_so_far.index(max_peak_ang)]
        
        prev_red_point_ang = (max_angle, max_peak_ang)
        ax3.plot(max_angle, max_peak_ang, 'ro')
        
        is_max_point_appropriate = Confirm_Maximum_Point()
        if is_max_point_appropriate:
            xl_max_ang_peak = max_peak_ang
            xl_max_ang_angle = np.degrees(max_angle)
            #print(xl_max_ang_angle, xl_max_ang_peak)
        if not is_max_point_appropriate:
            messagebox.showinfo("Info", "Please click on the Graph to select the correct Maximum Point.")
            plt.waitforbuttonpress()
            xl_max_ang_peak = new_max_peak_ang
            xl_max_ang_angle = np.degrees(new_max_angle)
            #print(xl_max_ang_peak, xl_max_ang_angle)
            
        q_write_ang = queue.Queue()
        Threaded_Function(Write_Angle_Dictionary_To_Excel, q_write_ang, peak_ang_dict, freq, f'peak_ang_data_{freq:.2f}MHz.xlsx')
        q_write_ang.get()
        
        if xl_max_ht_peak >= xl_max_ang_peak:
            final_peak_list.append(xl_max_ht_peak)
            deviation = limits - xl_max_ht_peak
            deviations_list.append(deviation)
        else:
            final_peak_list.append(xl_max_ang_peak)
            deviation = limits - xl_max_ang_peak
            deviations_list.append(deviation)
        
        freq_list.append(freq)
        max_ht_height_list.append(xl_max_ht_height)
        max_ht_list.append(xl_max_ht_peak)
        max_ang_angle_list.append(xl_max_ang_angle)
        max_ang_list.append(xl_max_ang_peak)
        
        Show_Popup()
        
        # user_response = Show_Popup()

        # if not user_response:
        #     # If the user clicks 'No', break the loop
        #     break
    Write_To_Excel(file_name, freq_list, max_ht_height_list, max_ht_list, max_ang_angle_list, max_ang_list, final_peak_list, deviations_list)
    plt.show()

    AC.close()
    Rx.close()
    
def Height_Scan(freq): # Performs ONLY Height Scan
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx_Auto(Rx_Addr)
    AC = Initialize_AC(AC_Addr)
    freq = float(manual_freq_entry.get())
    #measurement_parameters = Read_From_Excel(file_name)

    # freq_list = []
    # max_ht_list = []
    # max_ht_height_list = []
    heights_so_far = []
    peaks_so_far = []
    # max_ht_list = []
    # max_ht_height_list = []

    fig = plt.figure()
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    ax = fig.add_subplot(111)
    fig.canvas.mpl_connect('button_press_event', lambda event: On_Click_Height(event, ax, peaks_so_far, heights_so_far))
    line, = ax.plot([], [], lw=2)
    ax.set_title("Quasi Peak vs Height")
    ax.set_xlabel("Quasi Peak Value (dBµV/m)")
    ax.set_ylabel("Antenna Mast Height (cm)")
    ax.grid(True)

    #for params in measurement_parameters:
    #freq, sac, polarization = params
    global prev_red_point
    prev_red_point = None
    heights_so_far = []
    peaks_so_far = []

    ax.clear()
    
    data_queue_ht = queue.Queue()
    ht_thread = Threaded_Function(Height_Scan_With_Peak, data_queue_ht, AC, Rx, freq, data_queue_ht)
    while ht_thread.is_alive():
        try:
            current_position, peak_value = data_queue_ht.get(timeout=0.1)
            if peak_value > 0:
                heights_so_far.append(current_position)
                peaks_so_far.append(peak_value)
                ax.plot(peaks_so_far, heights_so_far, 'b-')
                ax.plot(peak_value, current_position, 'bo')
                ax.set_title(f"Quasi Peak vs Height for {freq} MHz")
                ax.set_xlabel("Quasi Peak Value (dBµV/m)")
                ax.set_ylabel("Antenna Mast Height (cm)")
                plt.pause(0.1)
        except queue.Empty:
            pass
    window.update_idletasks()
    window.update()

    ht_thread.join()
    peak_ht_dict = data_queue_ht.get()
    
    max_peak = max(peaks_so_far)
    max_height = heights_so_far[peaks_so_far.index(max_peak)]
    
    prev_red_point = (max_peak, max_height)
    ax.plot(max_peak, max_height, 'ro')
    
    is_max_point_appropriate = Confirm_Maximum_Point()
    if is_max_point_appropriate:
        xl_max_ht_peak = max_peak
        xl_max_ht_height = max_height
        #print(xl_max_ht_peak, xl_max_ht_height)
        Set_Height_And_Wait(AC, max_height)
    if not is_max_point_appropriate:
        messagebox.showinfo("Info", "Please click on the Graph to select the Correct Maximum Point.")
        plt.waitforbuttonpress()
        xl_max_ht_peak = new_max_peak
        xl_max_ht_height = new_max_height
        #print(xl_max_ht_peak, xl_max_ht_height)
    
    q_write_ht = queue.Queue()
    Threaded_Function(Write_Height_Dictionary_To_Excel, q_write_ht, peak_ht_dict, freq, f'peak_ht_data_{freq:.2f}MHz.xlsx')
    q_write_ht.get()
        
    plt.show()

    AC.close()
    Rx.close()

def Angle_Scan_Turndisc(freq): # Performs ONLY Angle Scan for Turndisc
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx_Auto(Rx_Addr)
    AC = Initialize_AC(AC_Addr)
    freq = float(manual_freq_entry.get())
    #measurement_parameters = Read_From_Excel(file_name)

    # freq_list = []
    # max_ang_list = []
    # max_ang_angle_list = []
    angles_so_far = []
    peaks_ang_so_far = []
    # max_ang_list = []
    # max_ang_angle_list = []

    fig = plt.figure()
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    ax = fig.add_subplot(111, projection='polar')
    fig.canvas.mpl_connect('button_press_event', lambda event: On_Click_Angle(event, ax, peaks_ang_so_far, angles_so_far))
    line, = ax.plot([], [], lw=2)
    ax.set_title("Angle vs Quasi Peak Polar Plot")
    ax.grid(True)

    #for params in measurement_parameters:
    #freq, sac, polarization = params
    global prev_red_point_ang
    prev_red_point_ang = None
    angles_so_far = []
    peaks_ang_so_far = []
    ax.clear()
    
    data_queue_ang = queue.Queue()
    ang_thread = Threaded_Function(Angle_Scan_With_Peak_Turndisc, data_queue_ang, AC, Rx, freq, data_queue_ang)
    while ang_thread.is_alive():
        try:
            current_position, peak_value = data_queue_ang.get(timeout=0.1)
            if peak_value > 0:
                angles_so_far.append(np.radians(current_position))
                peaks_ang_so_far.append(peak_value)
                ax.plot(angles_so_far, peaks_ang_so_far, 'b-')
                ax.plot(np.radians(current_position), peak_value, 'bo')
                ax.set_title(f"Angle vs Quasi Peak Polar Plot for {freq} MHz")
                plt.pause(0.1)
        except queue.Empty:
            pass
        window.update_idletasks()
        window.update()
    ang_thread.join()
    peak_ang_dict = data_queue_ang.get()

    max_peak_ang = max(peaks_ang_so_far)
    max_angle = angles_so_far[peaks_ang_so_far.index(max_peak_ang)]
    
    prev_red_point_ang = (max_angle, max_peak_ang)
    ax.plot(max_angle, max_peak_ang, 'ro')
    
    is_max_point_appropriate = Confirm_Maximum_Point()
    if is_max_point_appropriate:
        xl_max_ang_peak = max_peak_ang
        xl_max_ang_angle = np.degrees(max_angle)
        print(xl_max_ang_angle, xl_max_ang_peak)
    if not is_max_point_appropriate:
        messagebox.showinfo("Info", "Please click on the Graph to select the Correct Maximum Point.")
        plt.waitforbuttonpress()
        xl_max_ang_peak = new_max_peak_ang
        xl_max_ang_angle = np.degrees(new_max_angle)
        print(xl_max_ang_peak, xl_max_ang_angle)
        
    q_write_ang = queue.Queue()
    Threaded_Function(Write_Angle_Dictionary_To_Excel, q_write_ang, peak_ang_dict, freq, f'peak_ang_data_{freq:.2f}MHz.xlsx')
    q_write_ang.get()

    plt.show()

    AC.close()
    Rx.close()
    
def Angle_Scan_Turntable(freq): # Performs ONLY Angle Scan for Turntable
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx_Auto(Rx_Addr)
    AC = Initialize_AC(AC_Addr)
    #measurement_parameters = Read_From_Excel(file_name)
    freq = float(manual_freq_entry.get())

    #freq_list = []
    # max_ang_list = []
    # max_ang_angle_list = []
    angles_so_far = []
    peaks_ang_so_far = []
    # max_ang_list = []
    # max_ang_angle_list = []

    fig = plt.figure()
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    ax = fig.add_subplot(111, projection='polar')
    fig.canvas.mpl_connect('button_press_event', lambda event: On_Click_Angle(event, ax, peaks_ang_so_far, angles_so_far))
    line, = ax.plot([], [], lw=2)
    ax.set_title("Angle vs Quasi Peak Polar Plot")
    ax.grid(True)

    #for params in measurement_parameters:
    #freq, sac, polarization = params
    global prev_red_point_ang
    prev_red_point_ang = None
    angles_so_far = []
    peaks_ang_so_far = []

    ax.clear()
    
    data_queue_ang = queue.Queue()
    ang_thread = Threaded_Function(Angle_Scan_With_Peak_Turntable, data_queue_ang, AC, Rx, freq, data_queue_ang)
    while ang_thread.is_alive():
        try:
            current_position, peak_value = data_queue_ang.get(timeout=0.1)
            if peak_value > 0:
                angles_so_far.append(np.radians(current_position))
                peaks_ang_so_far.append(peak_value)
                ax.plot(angles_so_far, peaks_ang_so_far, 'b-')
                ax.plot(np.radians(current_position), peak_value, 'bo')
                ax.set_title(f"Angle vs Quasi Peak Polar Plot for {freq} MHz")
                plt.pause(0.1)
        except queue.Empty:
            pass
        window.update_idletasks()
        window.update()
    ang_thread.join()
    peak_ang_dict = data_queue_ang.get()

    max_peak_ang = max(peaks_ang_so_far)
    max_angle = angles_so_far[peaks_ang_so_far.index(max_peak_ang)]
    
    prev_red_point_ang = (max_angle, max_peak_ang)
    ax.plot(max_angle, max_peak_ang, 'ro')
    
    is_max_point_appropriate = Confirm_Maximum_Point()
    if is_max_point_appropriate:
        xl_max_ang_peak = max_peak_ang
        xl_max_ang_angle = np.degrees(max_angle)
        print(xl_max_ang_angle, xl_max_ang_peak)
    if not is_max_point_appropriate:
        messagebox.showinfo("Info", "Please click on the Graph to select the Correct Maximum Point.")
        plt.waitforbuttonpress()
        xl_max_ang_peak = new_max_peak_ang
        xl_max_ang_angle = np.degrees(new_max_angle)
        print(xl_max_ang_peak, xl_max_ang_angle)
        
    q_write_ang = queue.Queue()
    Threaded_Function(Write_Angle_Dictionary_To_Excel, q_write_ang, peak_ang_dict, freq, f'peak_ang_data_{freq:.2f}MHz.xlsx')
    q_write_ang.get()

    plt.show()

    AC.close()
    Rx.close()
##############################################################################
###################      FUNCTION CHECK            ###########################
##############################################################################
def Function_Check_Read_Excel_File(file_name): # Reads Excel File for Function Check
    df = pd.read_excel(file_name, usecols=[0, 1])
    frequencies = df.iloc[:, 0].tolist()
    sac_ref_vals = df.iloc[:, 1].tolist()
    measurement_parameters = list(zip(frequencies, sac_ref_vals))
    return measurement_parameters

def Function_Check_Write_Peak_Values_To_Excel(file_name, frequencies, reference_values, peak_values, deviations):
    df = pd.read_excel(file_name)
    
    # Ensure that the lengths of peak_values and deviations match the length of the DataFrame's index
    if len(peak_values) != len(df):
        peak_values += ["No Data Found"] * (len(df) - len(peak_values))
        
    if len(deviations) != len(df):
        deviations += ["No Data Found"] * (len(df) - len(deviations))
        
    df['Max Peak Values [dBuV]'] = peak_values
    df['Deviations [dBuV]'] = deviations
    
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    File_Name = f"{file_name}_{current_datetime}.xlsx"
    df.to_excel(File_Name, index=False)


def Function_Check_Scan(AC, Rx, Freq): # Performs Height Scan for Function Check
    Set_Freq(Freq, Rx)
    peaks_list = []
    #p=0
    max_peak = 0
    p = Query_Mast_Position(AC)
    if p <= 100.5:
        Send_Cmd(AC, "LD 400 CM NP")
        Send_Cmd(AC, "GO")
        while True:
            current_position = Query_Mast_Position(AC)
            peak_value = Get_Max_Peaks(Rx)
            peaks_list.append(peak_value)
            if current_position >= 389.7:
                break
            time.sleep(0.5)
    elif p >= 389.7:
        Send_Cmd(AC, "LD 100 CM NP")
        Send_Cmd(AC, "GO")
        while True:
            current_position = Query_Mast_Position(AC)
            peak_value = Get_Max_Peaks(Rx)
            peaks_list.append(peak_value)
            if current_position <= 100.1:
                break
            time.sleep(0.5)
    filtered_peaks = [peak for peak in peaks_list if 0 <= peak <= 1000]
    max_peak = max(filtered_peaks)
    if filtered_peaks:
        max_peak = max(filtered_peaks)
    else:
        max_peak = "No Data Found"
    return max_peak

def Function_Check_Scan_Threaded(AC, Rx, freq, result_queue): # Implements multithreading to the Height Scan
    max_peak = Function_Check_Scan(AC, Rx, freq)
    Wait_For_Stop(AC)
    result_queue.put(max_peak)

def Function_Check(file_name): # Performance Function Check
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    #frequencies, reference_values_list = Function_Check_Read_Excel_File(file_name)
    Rx = Initialize_Rx_Auto(Rx_Addr)
    AC = Initialize_AC(AC_Addr)
    measurement_parameters = Function_Check_Read_Excel_File(file_name)
    window.iconify()
    
    peaks_list = []
    freqs_list = []
    ref_vals_list = []
    deviations_list = []
    
    plt.ion()  # Turn on interactive mode
    fig, ax = plt.subplots()
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed') 
    ax.axhline(y=3, color='purple', linestyle='--', label='+3 dB')
    ax.axhline(y=-3, color='purple', linestyle='--', label='-3 dB')
    ax.grid(True)

    for params in measurement_parameters:
        freq, ref_values = params
        upper_bound = ref_values + 3
        lower_bound = ref_values - 3
        
        data_queue_fc = queue.Queue()
        fc_thread = Threaded_Function(Function_Check_Scan_Threaded, data_queue_fc, AC, Rx, freq, data_queue_fc)
        while fc_thread.is_alive():
            try:
                peak_value = data_queue_fc.get(timeout=0.1)
                if peak_value > 0:
                    freqs_list.append(freq)
                    peaks_list.append(peak_value)
                    ref_vals_list.append(ref_values)
                    deviation = peak_value - ref_values
                    deviations_list.append(deviation)
                    ax.semilogx(freqs_list, peaks_list, 'b-')
                    ax.semilogx(freq, peak_value,'bo')
                    ax.semilogx(freqs_list, ref_vals_list, 'g-')
                    ax.semilogx(freq, ref_values,'go')
                    ax.semilogx(freqs_list, deviations_list, 'r-')
                    ax.semilogx(freq, deviation,'ro')
                    ax.semilogx(freq, upper_bound, 'purple')  # upper bound (green triangle)
                    ax.semilogx(freq, lower_bound, 'purple')  # lower bound (red triangle)
                    ax.set_title("Function Check OATS")
                    ax.set_ylabel("Max Peak Value (dBµV/m)")
                    ax.set_xlabel("Frequency (MHz)")
                    plt.pause(0.1)
            except queue.Empty:
                pass
        window.update_idletasks()
        window.update()
        fc_thread.join()
        ax.semilogx(freqs_list, [ref + 3 for ref in ref_vals_list], color='purple', linestyle='--')  # line through upper bounds
        ax.semilogx(freqs_list, [ref - 3 for ref in ref_vals_list], color='purple', linestyle='--')
        # peaks_list.append(peak_value)
        # freqs_list.append(freq)
        # ref_vals_list.append(ref_values)
        # deviations_list.append(deviation)
        
        Show_Popup()

    Function_Check_Write_Peak_Values_To_Excel(file_name, freqs_list, ref_vals_list, peaks_list, deviations_list)

    plt.ioff()
    plt.show()

    AC.close()
    Rx.close()
##############################################################################
###################           UI FUNCTIONS           #########################
##############################################################################
window = tk.Tk()
window.title("Radiated Emissions Measurement")
window.geometry("1280x720")
window.configure(bg="#333333")
window.state('zoomed')
###############################################################################
#################         ANTENNA CONTROLLER         ##########################
###############################################################################
ac_frame = tk.Frame(window, bg="#333333")
ac_frame.pack(side="left", padx=20, pady=20, anchor="nw")
tk.Label(ac_frame, text="ANTENNA CONTROLLER", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="center")
#########################    INITIALIZE      ##################################
ac_address_frame = tk.Frame(ac_frame, bg="#333333")
ac_address_frame.pack(anchor="w", pady=10)
tk.Label(ac_address_frame, text="Address:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
ac_address_entry = tk.Entry(ac_address_frame)
ac_address_entry.pack(side="left")
ac_address_entry.insert(0, "GPIB1::7::INSTR")
def Initialize_Antenna_Controller():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    return AC
ac_init_button = tk.Button(ac_address_frame, text="Initialize", command=Initialize_Antenna_Controller)
ac_init_button.pack(padx=(5, 0))
###############       SET POLARIZATION                 ########################
polarization_frame = tk.Frame(ac_frame, bg="#333333", pady=10)
polarization_frame.pack(anchor="w")
tk.Label(polarization_frame, text="Polarization:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left", padx=(0, 10))
polarization_var = tk.StringVar()
polarization_var.set("horizontal")
tk.Radiobutton(polarization_frame, text="Horizontal", variable=polarization_var, value="horizontal", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
tk.Radiobutton(polarization_frame, text="Vertical", variable=polarization_var, value="vertical", fg="#FFFFFF", bg="#333333", indicatoron=False, selectcolor="#333333").pack(side="left")
def Set_Polarization():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    selected_polarization = polarization_var.get()
    Send_Cmd(AC, "LD TMPM1 DV")
    if selected_polarization == "vertical":
        Send_Cmd(AC, "PV")
    else:
        Send_Cmd(AC, "PH")
    AC.close()
set_polarization_button = tk.Button(polarization_frame, text="Set", command=Set_Polarization)
set_polarization_button.pack(anchor="e", padx=(5, 0))
#######################     SET DISTANCE             ##########################
distance_frame = tk.Frame(ac_frame, bg="#333333", pady=10)
distance_frame.pack(anchor="w")
tk.Label(distance_frame, text="Distance:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left", padx=(0, 10))
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
set_distance_button = tk.Button(distance_frame, text="Set", command=Set_Distance)
set_distance_button.pack(anchor="e", padx=(5, 0))
####################         GO TO HEIGHT           ###########################
height_go_frame = tk.Frame(ac_frame, bg="#333333", pady=10)
height_go_frame.pack(anchor="w")
height_label = tk.Label(height_go_frame, text="Height (Centimeters):", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
height_entry = tk.Entry(height_go_frame)
height_entry.pack(side="left")
def Go_To_Height():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    height = float(height_entry.get())
    Send_Cmd(AC, "LD TMPM1 DV")
    Send_Cmd(AC, f"LD {height} CM NP")
    Send_Cmd(AC, "GO")
go_height_button = tk.Button(height_go_frame, text="Go", command=Go_To_Height)
go_height_button.pack(padx=(5, 0))
####################         GO TO ANGLE            ###########################
angle_go_turndisc_frame = tk.Frame(ac_frame, bg="#333333")
angle_go_turndisc_frame.pack(anchor="w")
turndisc_angle_label = tk.Label(angle_go_turndisc_frame, text="Turndisc Angle (Degrees):", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
turndisc_angle_entry = tk.Entry(angle_go_turndisc_frame)
turndisc_angle_entry.pack(side="left")
def Go_To_Angle_Turndisc():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    angle = float(turndisc_angle_entry.get())
    Send_Cmd(AC, "LD DS1 DV")
    Send_Cmd(AC, f"LD {angle} DG NP GO")
turndisc_go_angle_button = tk.Button(angle_go_turndisc_frame, text="Go", command=Go_To_Angle_Turndisc)
turndisc_go_angle_button.pack(padx=(5, 0))

turntable_angle_go_frame = tk.Frame(ac_frame, bg="#333333")
turntable_angle_go_frame.pack(anchor="w")
turntable_angle_label = tk.Label(turntable_angle_go_frame, text="Turntable Angle (Degrees):", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
turntable_angle_entry = tk.Entry(turntable_angle_go_frame)
turntable_angle_entry.pack(side="left")
def Go_To_Angle_Turntable():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    angle = float(turntable_angle_entry.get())
    Send_Cmd(AC, "LD DT1 DV")
    Send_Cmd(AC, f"LD {angle} DG NP GO")
go_angle_button = tk.Button(turntable_angle_go_frame, text="Go", command=Go_To_Angle_Turntable)
go_angle_button.pack(padx=(5, 0))
#####################         RESET HEIGHT         ############################
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
reset_height_button.pack(anchor="center", padx=(5, 0), pady=5)
###############     RESET TURNDISC       ######################################
angle_reset_frame = tk.Frame(reset_frame, bg="#333333", pady=5)
angle_reset_frame.pack(anchor="w")
def Reset_Turndisc_Angle_UI():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    Send_Cmd(AC, "LD DS1 DV")
    Send_Cmd(AC, "LD 0 DG NP GO")
    AC.close()
reset_turndisc_angle_button = tk.Button(angle_reset_frame, text="Reset Turndisc to 0°", command=Reset_Turndisc_Angle_UI)
reset_turndisc_angle_button.pack(side="left", padx=(5, 0))
#############     RESET TURNTABLE       ######################################
def Reset_Turntable_Angle_UI():
    AC_Addr = ac_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    Send_Cmd(AC, "LD DT1 DV")
    Send_Cmd(AC, "LD 0 DG NP GO")
    AC.close()
reset_turntable_angle_button = tk.Button(angle_reset_frame, text="Reset Turntable to 0°", command=Reset_Turntable_Angle_UI)
reset_turntable_angle_button.pack(side="right", padx=(5, 0))
##############################################################################
##################        FUNCTION CHECK                ######################
##############################################################################
function_check_frame = tk.Frame(ac_frame, bg="#333333")
function_check_frame.pack(side="left", padx=20, pady=20, anchor="sw")
tk.Label(function_check_frame, text="FUNCTION CHECK", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="center")

file_fc_frame = tk.Frame(function_check_frame, bg="#333333")
file_fc_frame.pack()
entry_file = tk.Entry(file_fc_frame, font=("Arial", 12))
entry_file.pack(side=tk.LEFT, padx=5)

def Function_Check_Browse_File():
    FC_File_Name = fd.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xlsm")])
    if FC_File_Name:
        entry_file.delete(0, tk.END)  # Use entry_file here
        entry_file.insert(0, FC_File_Name)
button_browse = tk.Button(file_fc_frame, text="Browse", font=("Arial", 10), command=Function_Check_Browse_File)
button_browse.pack(side=tk.RIGHT, padx=5)
def Function_Check_UI():
    # Get the file name from the entry field
    FC_File_Name = entry_file.get()
    Function_Check(FC_File_Name)
button_start = tk.Button(function_check_frame, text="Start Function Check", font=("Arial", 10, "bold"), command=Function_Check_UI)
button_start.pack(pady=5)
###############################################################################
######################        RECEIVER             ############################
###############################################################################
rx_frame = tk.Frame(window, bg="#333333")
rx_frame.pack(side="left", padx=20, pady=20, anchor="nw")
tk.Label(rx_frame, text="RECEIVER", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="center")
#########################    INITIALIZE      ##################################
rx_address_frame = tk.Frame(rx_frame, bg="#333333")
rx_address_frame.pack(anchor="w", pady=10)
rx_address_label = tk.Label(rx_address_frame, text="Address:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
rx_address_entry = tk.Entry(rx_address_frame, width = 40)
rx_address_entry.pack(side="left")
rx_address_entry.insert(0, "USB0::0x2A8D::0x0F0B::MY59050129::0::INSTR")
def Initialize_Receiver():
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx(Rx_Addr)
    return Rx
rx_init_button = tk.Button(rx_address_frame, text="Initialize", command=Initialize_Receiver)
rx_init_button.pack(padx=5)
################            STATE         #####################################
state_frame = tk.Frame(rx_frame, bg="#333333")
state_frame.pack(anchor="w")
state_label = tk.Label(state_frame, text="State Number:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
state_entry = tk.Entry(state_frame, width = 15)
state_entry.pack(side="left")
state_entry.insert(0, "6")
def Set_Receiver_State():
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx(Rx_Addr)
    state = state_entry.get()
    Send_Cmd(Rx, f"*RCL {state}")
    return state
state_button = tk.Button(state_frame, text="Set", command=Set_Receiver_State)
state_button.pack(padx=5)
####################       RESOLUTION BANDWIDTH       ########################
res_bw_frame = tk.Frame(rx_frame, bg="#333333")
res_bw_frame.pack(anchor="w")
tk.Label(res_bw_frame, text="Resolution Bandwidth (kHz):", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
res_bw_entry = tk.Entry(res_bw_frame, width = 15)
res_bw_entry.pack(side="left")
res_bw_entry.insert(0, "120")
def Set_Resolution_Bandwidth():
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx(Rx_Addr)
    Res_BW = res_bw_entry.get()
    Send_Cmd(Rx, f"BAND {Res_BW} KHZ")
    return Res_BW
res_bw_button = tk.Button(res_bw_frame, text="Set", command=Set_Resolution_Bandwidth)
res_bw_button.pack(padx=5, pady=10)
####################       MECHANICAL ATTENUATION       ######################
attenuation_frame = tk.Frame(rx_frame, bg="#333333")
attenuation_frame.pack(anchor="w")
tk.Label(attenuation_frame, text="Attenuation (in dB):", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
attenuation_entry = tk.Entry(attenuation_frame, width = 15)
attenuation_entry.pack(side="left")
attenuation_entry.insert(0, "20")
def Set_Attenuation():
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx(Rx_Addr)
    Attenuation = attenuation_entry.get()
    Send_Cmd(Rx, f"POW:ATT {Attenuation}")
    return Attenuation
attenuation_button = tk.Button(attenuation_frame, text="Set", command=Set_Attenuation)
attenuation_button.pack(padx=5, pady=10)
################            MODE         ######################################
mode_frame = tk.Frame(rx_frame, bg="#333333", pady=10)
mode_frame.pack(anchor="w")
tk.Label(mode_frame, text="Mode:", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left", padx=(0, 10))
mode_var = tk.StringVar()
mode_var.set("Emi Receiver")  # Default value
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
set_mode_button = tk.Button(mode_frame, text="Set", command=Set_Mode)
set_mode_button.pack(anchor="e", padx=(10, 0))
###################     PEAK TYPES         ####################################
# def Get_Max_Peaks(Rx):
#     Send_Cmd(Rx, ":CALC:MARK1:MAX")
#     Send_Cmd(Rx, ":CALC:MARK1:Y?")
#     response = Read_Response(Rx)
#     Pk = float(response)
#     return Pk
# def Get_Average_Peaks(Rx):
#     Send_Cmd(Rx, "MARK2:TRAC3:TYPE AVER")
#     Send_Cmd(Rx, ":CALC:MAM:DET AVER")
#     Send_Cmd(Rx, ":CALC:MARK3:Y?")
#     response = Read_Response(Rx)
#     Avg = float(response)
#     return Avg
def Read_Max_Peaks(Rx):
    Send_Cmd(Rx, ":CALC:MARK1:Y?")
    response = Read_Response(Rx)
    peak = float(response)
    return peak

def Get_Max_Peaks(Rx):
    peaks = []
    for _ in range(3):
        peak = Read_Max_Peaks(Rx)
        peaks.append(peak)
        time.sleep(.05)
    Max = max(peaks)
    return Max

def Read_Average_Peaks(Rx):
    Send_Cmd(Rx, ":CALC:MARK3:Y?")
    response = Read_Response(Rx)
    peak = float(response)
    return peak

def Get_Average_Peaks(Rx):
    peaks = []
    for _ in range(3):
        peak = Read_Average_Peaks(Rx)
        peaks.append(peak)
        time.sleep(.05)
    Avg = max(peaks)
    return Avg

peak_type_frame = tk.Frame(rx_frame, bg="#333333", pady=10)
peak_type_frame.pack(anchor="w")
tk.Label(peak_type_frame, text="Peak: ", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left", padx=(0, 10))
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
set_peak_button = tk.Button(peak_type_frame, text="Set", command=Handle_Peak_Type_Selection)
set_peak_button.pack(anchor="e", padx=(10, 0))
####################         INITIALIZE TRACES        ########################
# def Initialize_Traces(Rx):
#     Send_Cmd(Rx, ":INIT:CONT ON")
#     Send_Cmd(Rx, "TRAC1:TYPE WRIT")
# def Initialize_Traces_UI():
#     Rx_Addr = rx_address_entry.get()
#     Rx = Initialize_Rx(Rx_Addr)
#     Initialize_Traces(Rx)
#     Rx.close()
# init_traces_button = tk.Button(rx_frame, text="Initialize Traces", width=15, pady=15, command = Initialize_Traces_UI)
# init_traces_button.pack(anchor="center")
###############################################################################
##################       MEASUREMENT            ###############################
###############################################################################
measurement_frame = tk.Frame(window, bg="#333333")
measurement_frame.pack(anchor="center", padx=20, pady=20)
tk.Label(measurement_frame, text="MEASUREMENT", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="center")
###################### AUTOMATIC MEASUREMENT        ###########################
auto_meas_frame = tk.Frame(measurement_frame, bg="#333333")
auto_meas_frame.pack(anchor="w")#, pady=10)
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
browse_file_button.pack(side="left", padx=(10, 0), pady=(0,5))

def Measurement_Turndisc(window):
    file_name = select_file_entry.get()
    Read_From_Excel(file_name)
    Auto_Measure_Turndisc(file_name, window)
start_turndisc_button = tk.Button(auto_meas_frame, text="Start Measurement at 3m (Turndisc)", font=("Arial", 10, "bold"), command=lambda: Measurement_Turndisc(window))
start_turndisc_button.pack(pady=(0,5))

def Measurement_Turntable(window):
    file_name = select_file_entry.get()
    Read_From_Excel(file_name)
    Auto_Measure_Turntable(file_name, window)
start_turntable_button = tk.Button(auto_meas_frame, text="Start Measurement at 10m (Turntable)", font=("Arial", 10, "bold"), command=lambda: Measurement_Turntable(window))
start_turntable_button.pack()
##############         MANUAL MEASUREMENT              ########################
manual_meas_frame = tk.Frame(measurement_frame, bg="#333333")
manual_meas_frame.pack(anchor="w", pady=10)
tk.Label(manual_meas_frame, text="Manual Measurement", font=("Arial", 16, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="w")

enter_freq_frame = tk.Frame(manual_meas_frame, bg="#333333")
enter_freq_frame.pack(anchor="w", pady=5)
tk.Label(enter_freq_frame, text="Enter Frequency (MHz):", font=("Arial", 10, "bold"), fg="#FFFFFF", bg="#333333").pack(side="left")
manual_freq_entry = tk.Entry(enter_freq_frame, width=15)
manual_freq_entry.pack(side="left")
def Set_Manual_Frequency():
    selected_freq = float(manual_freq_entry.get())
    Rx_Addr = rx_address_entry.get()
    Rx = Initialize_Rx(Rx_Addr)
    Set_Freq(selected_freq, Rx)
    Rx.close()
set_manual_freq_button = tk.Button(enter_freq_frame, text="Set", command=Set_Manual_Frequency)
set_manual_freq_button.pack(side="left", padx=(10, 0))

def Height_Scan_UI():
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    Rx = Initialize_Rx_Auto(Rx_Addr)
    freq = float(manual_freq_entry.get())
    Height_Scan(freq)
    AC.close()
    Rx.close()
height_scan_button = tk.Button(manual_meas_frame, text="Height Scan", font=("Arial", 10, "bold"), width=10, command = Height_Scan_UI)
height_scan_button.pack(side="left")

def Angle_Scan_Turndisc_UI():
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    Rx = Initialize_Rx_Auto(Rx_Addr)
    freq = float(manual_freq_entry.get())
    Angle_Scan_Turndisc(freq)
    AC.close()
    Rx.close()
angle_scan_td_button = tk.Button(manual_meas_frame, text="3m Scan (Turndisc)", font=("Arial", 10, "bold"), width=20, command = Angle_Scan_Turndisc_UI)
angle_scan_td_button.pack(side="left", padx=(20, 0))

def Angle_Scan_Turntable_UI():
    AC_Addr = ac_address_entry.get()
    Rx_Addr = rx_address_entry.get()
    AC = Initialize_AC(AC_Addr)
    Rx = Initialize_Rx_Auto(Rx_Addr)
    freq = float(manual_freq_entry.get())
    Angle_Scan_Turntable(freq)
    AC.close()
    Rx.close()
angle_scan_tt_button = tk.Button(manual_meas_frame, text="10m Scan (Turntable)", font=("Arial", 10, "bold"), width=20, command = Angle_Scan_Turntable_UI)
angle_scan_tt_button.pack(side="right", padx=(20, 0))
################################      GRAPHS          #########################
graphs_frame = tk.Frame(measurement_frame, bg="#333333")
graphs_frame.pack(anchor="w", pady=10)
tk.Label(graphs_frame, text="Plot Graphs", font=("Arial", 16, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="w")
#tk.Label(graphs_frame, text="Plot Graphs", font=("Arial", 16, "bold"), fg="#FFFFFF", bg="#333333").pack(anchor="w", pady=(0,10))
height_file_frame = tk.Frame(graphs_frame, bg="#333333")
height_file_frame.pack(anchor="w")
height_file_entry = tk.Entry(height_file_frame, width=45)
height_file_entry.pack(side="left")
def Browse_Height_File():
    Height_File_Name = fd.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xlsm")])
    if Height_File_Name:
        height_file_entry.delete(0, tk.END)
        height_file_entry.insert(0, Height_File_Name)
browse_height_file_button = tk.Button(height_file_frame, text="Browse Height File", width=15, command=Browse_Height_File)
browse_height_file_button.pack(side="left", padx=(10, 0))
def Plot_Height_Graph():
    height_file_name = height_file_entry.get()
    Plot_Height_vs_Peak(height_file_name)
plot_height_graph_button = tk.Button(height_file_frame, text="Plot", width=10, command=Plot_Height_Graph)
plot_height_graph_button.pack(side="left", padx=(10, 0))

angle_file_frame = tk.Frame(graphs_frame, bg="#333333")
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
def Plot_Angle_Graph():
    angle_file_name = angle_file_entry.get()
    Plot_Angle_vs_Peak_Polar(angle_file_name)
plot_angle_graph_button = tk.Button(angle_file_frame, text="Plot", width=10, command=Plot_Angle_Graph)
plot_angle_graph_button.pack(side="left", padx=(10, 0))
##############################################################################
#####################       EXIT            ##################################
##############################################################################
exit_button = tk.Button(window, text="Exit", command=window.quit, width=5)
exit_button.pack(side="bottom", anchor="center")
window.mainloop()