#Import necessary libraries
import tkinter as tk
from tkinter import filedialog as fd
import pyvisa as pv
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Send command to the device
def Send_Cmd(device, command):
    device.write(command)

# Read response of the device
def Read_Response(device):
    response = device.read()
    return response
#######################################################