import serial
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk
from ttkthemes import ThemedStyle
import csv
import os
from tkinter import messagebox
from mcculw import ul
from mcculw.enums import ULRange
from mcculw.ul import ULError
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
import matplotlib.dates as mdates

# Set up the board number, channel, and AI range for USB-1208FS-Plus
board_num = 0
channel = 0
ai_range = ULRange.BIP5VOLTS

def acquire_data():
    try:
        # Get a value from the USB-1208FS-Plus device
        value = ul.a_in(board_num, channel, ai_range)
        # Convert the raw value to engineering units
        eng_units_value = ul.to_eng_units(board_num, ai_range, value)

        return eng_units_value
    except ULError as e:
        messagebox.showerror("UL Error", f"A UL error occurred. Code: {str(e.errorcode)} Message: {e.message}")
        return None

def process_data(response):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if response is not None:
        log_text.insert(tk.END, f"{timestamp} - Device: USB-1208FS-Plus - Value: {response}\n")
        write_to_csv(timestamp, "USB-1208FS-Plus", response)
        update_plot(timestamp, response)
    else:
        log_text.insert(tk.END, f"{timestamp} - Error occurred while acquiring data from USB-1208FS-Plus\n")

def write_to_csv(timestamp, device, value):
    file_path = "data.csv"
    is_file_exists = os.path.exists(file_path)
    with open(file_path, "a", newline="") as file:
        writer = csv.writer(file)
        if not is_file_exists:
            writer.writerow(["Timestamp", "Device", "Value"])
        writer.writerow([timestamp, device, value])

def data_acquisition():
    while not stop_flag.is_set():
        response = acquire_data()
        process_data(response)

def start_acquisition():
    # Clear the stop flag if it was set previously
    stop_flag.clear()

    # Create and start the data acquisition thread
    thread = threading.Thread(target=data_acquisition)
    thread.start()

    # Disable the start button and enable the stop button
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)

def stop_acquisition():
    # Set the stop flag to stop the acquisition process
    stop_flag.set()

    # Enable the start button and disable the stop button
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

def export_to_csv():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    if file_path:
        with open(file_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Device", "Value"])
            for item in log_text.get("1.0", tk.END).splitlines():
                if "Device: " in item and "Value: " in item:
                    timestamp, rest = item.split(" - ", 1)
                    device, value = rest.split(" - ")
                    device = device.split(": ")[1]
                    value = value.split(": ")[1]

                    writer.writerow([timestamp, device, value])

        log_text.insert(tk.END, "Log exported to {}\n".format(file_path))
    else:
        log_text.insert(tk.END, "Export cancelled\n")

def clear_data():
    log_text.delete("1.0", tk.END)
    ax.cla()
    canvas.draw()

def update_plot(timestamp, value):
    x_data.append(timestamp)
    y_data.append(value)
    ax.plot(x_data, y_data, color='b', marker='o')
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    ax.tick_params(axis='x', rotation=45)
    ax.relim()
    ax.autoscale_view()
    canvas.draw()

# Create the Tkinter GUI
root = tk.Tk()
root.title("Data Acquisition")

# Apply a modern theme to the GUI
style = ThemedStyle(root)
style.set_theme("arc")

# Create a Frame to hold the log text box and scrollbar
log_frame = ttk.Frame(root)
log_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a Text widget to display the log
log_text = tk.Text(log_frame, height=10, width=40)
log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create a scrollbar for the log window
scrollbar = ttk.Scrollbar(log_frame, command=log_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
log_text.config(yscrollcommand=scrollbar.set)

# Create a Figure for the plot
fig = Figure(figsize=(6, 4), dpi=100)
ax = fig.add_subplot(111)

# Create a canvas to display the plot
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Create a toolbar for the plot
toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Create a Frame to hold the buttons
button_frame = ttk.Frame(root)
button_frame.pack(pady=10)

# Start button to initiate data acquisition
start_button = ttk.Button(button_frame, text="Start Acquisition", command=start_acquisition)
start_button.pack(side=tk.LEFT)

# Stop button to stop the data acquisition process
stop_button = ttk.Button(button_frame, text="Stop Acquisition", command=stop_acquisition, state=tk.DISABLED)
stop_button.pack(side=tk.LEFT)

# Export button to export the log into a CSV file
export_button = ttk.Button(button_frame, text="Export to CSV", command=export_to_csv)
export_button.pack(side=tk.LEFT)

# Clear button to clear the log and graph
clear_button = ttk.Button(button_frame, text="Clear Data", command=clear_data)
clear_button.pack(side=tk.LEFT)

# Stop flag to indicate when to stop the acquisition process
stop_flag = threading.Event()

# Data lists for the plot
x_data = []
y_data = []

# Run the Tkinter event loop
root.mainloop()
