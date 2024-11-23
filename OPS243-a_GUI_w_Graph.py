import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import serial
import time
from collections import deque
import csv
import os
from datetime import datetime
import matplotlib
import threading
import traceback  # Import traceback for exception handling

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


# Set up the serial connection (adjust port and baud rate as needed)
SERIAL_PORT = '/dev/tty.usbmodem113301'  # Change this to your serial port
BAUD_RATE = 115200

class OPS243GUI:
    def __init__(self, root):
        try:
            print("Initializing OPS243GUI...")
            self.root = root
            self.root.title("OPS243-A Radar Sensor")
            self.root.geometry("800x600")  # Set default window size
            self.root.resizable(True, True)  # Allow window to be resizable

            # Create a notebook (tabbed interface)
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill='both', expand=True)

            # Create frames for each tab
            self.general_tab = ttk.Frame(self.notebook)
            self.graph_tab = ttk.Frame(self.notebook)
            self.cli_tab = ttk.Frame(self.notebook)

            # Add tabs to the notebook
            self.notebook.add(self.general_tab, text='General')
            self.notebook.add(self.graph_tab, text='Speed Graph')
            self.notebook.add(self.cli_tab, text='CLI')

            # Initialize data variables
            self.speed_value = 0.0
            self.direction_value = "N/A"
            self.max_speed = None
            self.min_speed = None
            self.speed_values = deque()
            self.start_time = None  # Will be set when recording starts
            self.running = False  # Will be set to True after successful connection
            self.display_unit = "km/h"  # Default display unit

            # Initialize configuration variables
            self.frequency = 0  # Default frequency setting (T=0)
            self.output_format = "Speed"  # Default output
            self.magnitude_filter = 0
            self.direction_filter = "Both"
            self.power_mode = "Active"

            # Initialize GUI update variables
            self.speed_text_value = "Speed: N/A"
            self.max_speed_text_value = "Max Speed: N/A"
            self.min_speed_text_value = "Min Speed: N/A"
            self.avg_speed_text_value = "Avg Speed (5s): N/A"

            # Graphing variables
            self.recording = False
            self.graph_data = []
            self.graph_start_time = None
            self.record_mode = tk.StringVar(value="Instantaneous")  # Default to Instantaneous

            # UI Elements
            self.create_widgets()

            # Start the connection in a separate thread
            threading.Thread(target=self.connect_to_sensor, daemon=True).start()
        except Exception as e:
            print(f"Exception in __init__: {e}")
            traceback.print_exc()

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_widgets(self):
        try:
            # General Tab
            self.info_text = tk.StringVar(value="Connecting to sensor...")
            self.info_label = tk.Label(self.general_tab, textvariable=self.info_text, justify="left", anchor="w")
            self.info_label.pack(anchor="w", fill='x')

            self.speed_text = tk.StringVar(value="Speed: N/A")
            self.max_speed_text = tk.StringVar(value="Max Speed: N/A")
            self.min_speed_text = tk.StringVar(value="Min Speed: N/A")
            self.avg_speed_text = tk.StringVar(value="Avg Speed (5s): N/A")
            self.direction_text = tk.StringVar(value="Direction: N/A")

            tk.Label(self.general_tab, textvariable=self.speed_text, anchor="w").pack(anchor="w", fill='x')
            tk.Label(self.general_tab, textvariable=self.max_speed_text, anchor="w").pack(anchor="w", fill='x')
            tk.Label(self.general_tab, textvariable=self.min_speed_text, anchor="w").pack(anchor="w", fill='x')
            tk.Label(self.general_tab, textvariable=self.avg_speed_text, anchor="w").pack(anchor="w", fill='x')
            tk.Label(self.general_tab, textvariable=self.direction_text, anchor="w").pack(anchor="w", fill='x')

            # Unit Toggle
            self.unit_var = tk.StringVar(value=self.display_unit)
            unit_frame = tk.Frame(self.general_tab)
            unit_frame.pack(anchor="w")
            tk.Label(unit_frame, text="Display Unit: ").pack(side="left")
            tk.Radiobutton(unit_frame, text="km/h", variable=self.unit_var, value="km/h", command=self.update_unit).pack(side="left")
            tk.Radiobutton(unit_frame, text="mph", variable=self.unit_var, value="mph", command=self.update_unit).pack(side="left")
            tk.Radiobutton(unit_frame, text="m/s", variable=self.unit_var, value="m/s", command=self.update_unit).pack(side="left")

            # Sensor Controls
            freq_frame = tk.Frame(self.general_tab)
            freq_frame.pack(anchor="w", pady=5)
            tk.Label(freq_frame, text="Frequency Control (T=n): ").pack(side="left")
            self.freq_var = tk.IntVar(value=self.frequency)
            self.freq_entry = tk.Entry(freq_frame, textvariable=self.freq_var, width=5)
            self.freq_entry.pack(side="left")
            tk.Button(freq_frame, text="Set Frequency", command=self.set_frequency).pack(side="left", padx=5)

            output_frame = tk.Frame(self.general_tab)
            output_frame.pack(anchor="w", pady=5)
            tk.Label(output_frame, text="Output Format: ").pack(side="left")
            self.output_var = tk.StringVar(value="Speed")
            tk.Radiobutton(output_frame, text="Speed", variable=self.output_var, value="Speed", command=self.set_output_format).pack(side="left")
            tk.Radiobutton(output_frame, text="FFT Output", variable=self.output_var, value="FFT", command=self.set_output_format).pack(side="left")
            tk.Radiobutton(output_frame, text="Raw ADC", variable=self.output_var, value="Raw", command=self.set_output_format).pack(side="left")

            mag_frame = tk.Frame(self.general_tab)
            mag_frame.pack(anchor="w", pady=5)
            tk.Label(mag_frame, text="Magnitude Filter (M>n): ").pack(side="left")
            self.mag_var = tk.IntVar(value=self.magnitude_filter)
            self.mag_entry = tk.Entry(mag_frame, textvariable=self.mag_var, width=5)
            self.mag_entry.pack(side="left")
            tk.Button(mag_frame, text="Set Magnitude Filter", command=self.set_magnitude_filter).pack(side="left", padx=5)

            dir_frame = tk.Frame(self.general_tab)
            dir_frame.pack(anchor="w", pady=5)
            tk.Label(dir_frame, text="Direction Filter: ").pack(side="left")
            self.dir_var = tk.StringVar(value=self.direction_filter)
            tk.Radiobutton(dir_frame, text="Both", variable=self.dir_var, value="Both", command=self.set_direction_filter).pack(side="left")
            tk.Radiobutton(dir_frame, text="Approaching", variable=self.dir_var, value="Approaching", command=self.set_direction_filter).pack(side="left")
            tk.Radiobutton(dir_frame, text="Receding", variable=self.dir_var, value="Receding", command=self.set_direction_filter).pack(side="left")

            power_frame = tk.Frame(self.general_tab)
            power_frame.pack(anchor="w", pady=5)
            tk.Label(power_frame, text="Power Mode: ").pack(side="left")
            self.power_var = tk.StringVar(value=self.power_mode)
            tk.Radiobutton(power_frame, text="Active", variable=self.power_var, value="Active", command=self.set_power_mode).pack(side="left")
            tk.Radiobutton(power_frame, text="Idle", variable=self.power_var, value="Idle", command=self.set_power_mode).pack(side="left")

            # Save and Reset Buttons
            settings_frame = tk.Frame(self.general_tab)
            settings_frame.pack(anchor="w", pady=5)
            tk.Button(settings_frame, text="Save Settings", command=self.save_settings).pack(side="left", padx=5)
            tk.Button(settings_frame, text="Reset Settings", command=self.reset_settings).pack(side="left", padx=5)

            # Speed Graph Tab
            graph_control_frame = tk.Frame(self.graph_tab)
            graph_control_frame.pack(anchor="w", pady=5)
            tk.Label(graph_control_frame, text="Filename Prefix: ").pack(side="left")
            self.filename_prefix_entry = tk.Entry(graph_control_frame, width=20)
            self.filename_prefix_entry.pack(side="left", padx=5)
            tk.Button(graph_control_frame, text="Start Recording", command=self.start_recording).pack(side="left", padx=5)
            tk.Button(graph_control_frame, text="Stop Recording", command=self.stop_recording).pack(side="left", padx=5)

            # Toggle for recording mode
            record_mode_frame = tk.Frame(self.graph_tab)
            record_mode_frame.pack(anchor="w", pady=5)
            tk.Label(record_mode_frame, text="Record Mode: ").pack(side="left")
            tk.Radiobutton(record_mode_frame, text="Instantaneous", variable=self.record_mode, value="Instantaneous").pack(side="left")
            tk.Radiobutton(record_mode_frame, text="Average", variable=self.record_mode, value="Average").pack(side="left")
            tk.Radiobutton(record_mode_frame, text="Both", variable=self.record_mode, value="Both").pack(side="left")  # Add option for both

            self.fig, self.ax = plt.subplots(figsize=(6, 4))
            self.ax.set_xlabel('Time (s)')
            self.ax.set_ylabel(f'Speed ({self.display_unit})')
            self.line_instant, = self.ax.plot([], [], 'b-', label='Instantaneous')  # Blue line for instantaneous
            self.line_avg, = self.ax.plot([], [], 'r-', label='Average')  # Red line for average
            self.ax.legend()
            self.graph_canvas = FigureCanvasTkAgg(self.fig, master=self.graph_tab)
            self.graph_canvas.get_tk_widget().pack(fill='both', expand=True)

            # CLI Tab
            self.command_entry = tk.Entry(self.cli_tab, width=50)
            self.command_entry.pack(side="top", padx=5, pady=5)
            self.command_entry.bind('<Return>', self.send_user_command)
            self.send_button = tk.Button(self.cli_tab, text="Send", command=self.send_user_command)
            self.send_button.pack(side="top", padx=5, pady=5)

            self.cli_text = tk.Text(self.cli_tab, state='disabled')
            self.cli_text.pack(fill='both', expand=True)
        except Exception as e:
            print(f"Exception in create_widgets: {e}")
            traceback.print_exc()

    def update_unit(self):
        try:
            self.display_unit = self.unit_var.get()
            print(f"Display unit changed to {self.display_unit}")
            if self.serial_connection:
                if self.display_unit == "km/h":
                    self.send_command("UK")
                elif self.display_unit == "mph":
                    self.send_command("US")
                elif self.display_unit == "m/s":
                    self.send_command("UM")
            # Update the displayed speed values
            self.root.after(0, self.update_gui)
            # Update graph's Y-axis label
            self.ax.set_ylabel(f'Speed ({self.display_unit})')
            self.canvas.draw()
        except Exception as e:
            print(f"Exception in update_unit: {e}")
            traceback.print_exc()

    def set_frequency(self):
        try:
            freq_value = self.freq_var.get()
            if -2 <= freq_value <= 2:
                command = f"T={freq_value}"
                self.send_command(command)
                self.frequency = freq_value
                print(f"Frequency set to T={freq_value}")
            else:
                messagebox.showerror("Invalid Frequency", "Frequency must be between -2 and 2.")
        except Exception as e:
            print(f"Exception in set_frequency: {e}")
            traceback.print_exc()

    def set_output_format(self):
        try:
            output_format = self.output_var.get()
            if output_format == "Speed":
                self.send_command("OS")  # Turn on speed reporting
                self.send_command("Of")  # Turn off FFT output
                self.send_command("Or")  # Turn off raw ADC output
            elif output_format == "FFT":
                self.send_command("Of")  # Turn on FFT output
                self.send_command("Os")  # Turn off speed reporting
                self.send_command("Or")  # Turn off raw ADC output
            elif output_format == "Raw":
                self.send_command("Or")  # Turn on raw ADC output
                self.send_command("Os")  # Turn off speed reporting
                self.send_command("Of")  # Turn off FFT output
            self.output_format = output_format
            print(f"Output format set to {output_format}")
        except Exception as e:
            print(f"Exception in set_output_format: {e}")
            traceback.print_exc()

    def set_magnitude_filter(self):
        try:
            mag_value = self.mag_var.get()
            command = f"M>{mag_value}"
            self.send_command(command)
            self.magnitude_filter = mag_value
            print(f"Magnitude filter set to M>{mag_value}")
        except Exception as e:
            print(f"Exception in set_magnitude_filter: {e}")
            traceback.print_exc()

    def set_direction_filter(self):
        try:
            direction = self.dir_var.get()
            if direction == "Both":
                self.send_command("R|")
            elif direction == "Approaching":
                self.send_command("R+")
            elif direction == "Receding":
                self.send_command("R-")
            self.direction_filter = direction
            print(f"Direction filter set to {direction}")
        except Exception as e:
            print(f"Exception in set_direction_filter: {e}")
            traceback.print_exc()

    def set_power_mode(self):
        try:
            power_mode = self.power_var.get()
            if power_mode == "Active":
                self.send_command("PA")
            elif power_mode == "Idle":
                self.send_command("PI")
            self.power_mode = power_mode
            print(f"Power mode set to {power_mode}")
        except Exception as e:
            print(f"Exception in set_power_mode: {e}")
            traceback.print_exc()

    def send_user_command(self, event=None):
        try:
            command = self.command_entry.get()
            if command and self.serial_connection:
                self.send_command(command)
                self.command_entry.delete(0, 'end')
        except Exception as e:
            print(f"Exception in send_user_command: {e}")
            traceback.print_exc()

    def connect_to_sensor(self):
        try:
            print("Attempting to connect to sensor...")
            self.serial_connection = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
            time.sleep(2)  # Allow time for the connection to establish
            # Since we're in a separate thread, use `self.root.after` to update the GUI
            self.root.after(0, lambda: self.info_text.set("Connected to OPS243-A sensor."))
            print("Sensor connected.")
            # Configure the sensor
            self.configure_sensor()
            # Start updates using threading
            self.running = True
            threading.Thread(target=self.update_stats, daemon=True).start()
            threading.Thread(target=self.calculate_avg_speed, daemon=True).start()
        except serial.SerialException as e:
            # Schedule the error dialog after the main loop has started
            self.root.after(0, lambda: messagebox.showerror("Connection Error", f"Failed to connect to sensor:\n{e}"))
            self.root.after(0, lambda: self.info_text.set("Failed to connect to sensor."))
            print(f"Failed to connect to sensor: {e}")
            self.running = False
        except Exception as e:
            print(f"Exception in connect_to_sensor: {e}")
            traceback.print_exc()

    def configure_sensor(self):
        try:
            if self.serial_connection:
                print("Configuring sensor...")
                # Set output units based on display unit
                if self.display_unit == "km/h":
                    self.send_command("UK")
                elif self.display_unit == "mph":
                    self.send_command("US")
                elif self.display_unit == "m/s":
                    self.send_command("UM")
                # Set default output format
                self.send_command("OS")  # Enable speed reporting
                # Set default magnitude filter
                self.send_command(f"M>{self.magnitude_filter}")
                # Set default direction filter
                self.set_direction_filter()
                # Apply other default settings as needed
                self.send_command("O1")  # Enable continuous output
                print("Sensor configured.")
        except Exception as e:
            print(f"Exception in configure_sensor: {e}")
            traceback.print_exc()

    def send_command(self, command):
        try:
            if self.serial_connection:
                full_command = f"{command}\n".encode('utf-8')
                self.serial_connection.write(full_command)
                time.sleep(0.05)  # Short delay
                # Read acknowledgment
                ack = self.serial_connection.readline().decode('utf-8').strip()
                response = f"Sent: {command}\nReceived: {ack}\n"
                print(response)
                # Schedule GUI update in the main thread
                self.root.after(0, lambda: self.update_cli(response))
        except Exception as e:
            print(f"Exception in send_command: {e}")
            self.root.after(0, lambda: self.update_cli(f"Error sending command: {e}\n"))
            traceback.print_exc()

    def update_cli(self, message):
        try:
            if self.cli_text.winfo_exists():
                self.cli_text.configure(state='normal')
                self.cli_text.insert('end', message)
                self.cli_text.configure(state='disabled')
                self.cli_text.see('end')  # Scroll to the end
        except Exception as e:
            print(f"Exception in update_cli: {e}")
            traceback.print_exc()

    def update_stats(self):
        while self.running and self.serial_connection:
            try:
                # Read a line from the serial port
                data_line = self.serial_connection.readline().decode('utf-8').strip()

                # Parse the data line
                if data_line and self.is_float(data_line):
                    speed_value = float(data_line)

                    # Determine direction based on sign
                    self.direction_value = "Approaching" if speed_value > 0 else "Receding"

                    # Use absolute value for speed
                    speed_value = abs(speed_value)

                    # Update max and min speed
                    self.max_speed = max(self.max_speed or speed_value, speed_value)
                    self.min_speed = min(self.min_speed or speed_value, speed_value)

                    # Add speed to deque with timestamp
                    self.speed_values.append((time.time(), speed_value))

                    # Prepare display values based on selected unit
                    speed_display, unit = self.convert_speed(speed_value)
                    max_speed_display, _ = self.convert_speed(self.max_speed)
                    min_speed_display, _ = self.convert_speed(self.min_speed)

                    self.speed_text_value = f"Speed: {speed_display:.2f} {unit}"
                    self.max_speed_text_value = f"Max Speed: {max_speed_display:.2f} {unit}"
                    self.min_speed_text_value = f"Min Speed: {min_speed_display:.2f} {unit}"

                    # Update the GUI labels
                    self.root.after(0, self.update_gui)

                    # If recording, add data to graph_data
                    if self.recording:
                        if self.graph_start_time is None:
                            self.graph_start_time = time.time()
                        elapsed_time = time.time() - self.graph_start_time
                        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                        if self.record_mode.get() == "Instantaneous":
                            self.graph_data.append({'Time': elapsed_time, 'Speed': speed_display, 'Timestamp': timestamp})
                        elif self.record_mode.get() == "Average":
                            avg_speed = sum(speed for _, speed in self.speed_values) / len(self.speed_values)
                            avg_speed_display, _ = self.convert_speed(avg_speed)
                            self.graph_data.append({'Time': elapsed_time, 'Speed': avg_speed_display, 'Timestamp': timestamp})
                        elif self.record_mode.get() == "Both":
                            avg_speed = sum(speed for _, speed in self.speed_values) / len(self.speed_values)
                            avg_speed_display, _ = self.convert_speed(avg_speed)
                            self.graph_data.append({'Time': elapsed_time, 'Speed': speed_display, 'Avg_Speed': avg_speed_display, 'Timestamp': timestamp})
                        self.root.after(0, self.update_graph)
                else:
                    # Invalid data received; skip updating the GUI
                    if data_line:
                        print(f"Invalid data received: '{data_line}'")
                        self.root.after(0, lambda: self.update_cli(f"Invalid data: {data_line}\n"))
                    pass  # Retain previous values

            except serial.SerialException as e:
                print(f"SerialException in update_stats: {e}")
                self.root.after(0, lambda: self.update_cli(f"Error: {e}\n"))
                self.running = False
            except Exception as e:
                print(f"Exception in update_stats: {e}")
                self.root.after(0, lambda: self.update_cli(f"Error: {e}\n"))
                traceback.print_exc()

            time.sleep(0.1)  # Sleep for 100 ms

    def calculate_avg_speed(self):
        while self.running:
            try:
                current_time = time.time()
                # Remove speed entries older than 5 seconds
                while self.speed_values and (current_time - self.speed_values[0][0]) > 5:
                    self.speed_values.popleft()
                # Calculate average speed
                if self.speed_values:
                    avg_speed = sum(speed for _, speed in self.speed_values) / len(self.speed_values)
                    avg_speed_display, unit = self.convert_speed(avg_speed)
                    self.avg_speed_text_value = f"Avg Speed (5s): {avg_speed_display:.2f} {unit}"
                else:
                    self.avg_speed_text_value = "Avg Speed (5s): N/A"
                # Update the GUI label
                self.root.after(0, self.update_avg_speed_gui)
            except Exception as e:
                print(f"Exception in calculate_avg_speed: {e}")
                traceback.print_exc()
            time.sleep(1.0)  # Sleep for 1 second

    def update_gui(self):
        try:
            self.speed_text.set(self.speed_text_value)
            self.max_speed_text.set(self.max_speed_text_value)
            self.min_speed_text.set(self.min_speed_text_value)
            self.direction_text.set(f"Direction: {self.direction_value}")
        except Exception as e:
            print(f"Exception in update_gui: {e}")
            traceback.print_exc()

    def update_avg_speed_gui(self):
        try:
            self.avg_speed_text.set(self.avg_speed_text_value)
        except Exception as e:
            print(f"Exception in update_avg_speed_gui: {e}")
            traceback.print_exc()

    def update_graph(self):
        try:
            times = [data['Time'] for data in self.graph_data]
            speeds = [data['Speed'] for data in self.graph_data]
            self.line_instant.set_data(times, speeds)
            if self.record_mode.get() == "Both":
                avg_speeds = [data['Avg_Speed'] for data in self.graph_data]
                self.line_avg.set_data(times, avg_speeds)
            self.ax.relim()
            self.ax.autoscale_view()
            self.graph_canvas.draw()
        except Exception as e:
            print(f"Exception in update_graph: {e}")
            traceback.print_exc()

    def start_recording(self):
        try:
            self.recording = True
            self.graph_data = []
            self.graph_start_time = time.time()
            filename_prefix = self.filename_prefix_entry.get()
            # Create a directory for saved files if it doesn't exist
            save_dir = os.path.join(os.getcwd(), "saved_graphs")
            os.makedirs(save_dir, exist_ok=True)
            self.filename = os.path.join(save_dir, f"{filename_prefix}_speed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            print(f"Recording started. Data will be saved to {self.filename}")
        except Exception as e:
            print(f"Exception in start_recording: {e}")
            traceback.print_exc()

    def stop_recording(self):
        try:
            self.recording = False
            if self.graph_data:
                filepath = self.filename
                # Save to CSV
                with open(filepath, 'w', newline='') as csvfile:
                    fieldnames = ['Time (s)', f'Speed ({self.display_unit})', 'Timestamp']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for data in self.graph_data:
                        writer.writerow({'Time (s)': data['Time'],
                                         f'Speed ({self.display_unit})': data['Speed'],
                                         'Timestamp': data['Timestamp']})
                messagebox.showinfo("Data Saved", f"Data saved to {filepath}")
                print(f"Data saved to {filepath}")
            else:
                print("No data recorded.")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data:\n{e}")
            print(f"Failed to save data: {e}")
            traceback.print_exc()

    def save_graph_data(self):
        try:
            if self.graph_data:
                # Create filename with date and time
                now = datetime.now()
                filename = now.strftime('speed_data_%Y%m%d_%H%M%S.csv')
                filepath = os.path.join(os.getcwd(), filename)
                # Save to CSV
                with open(filepath, 'w', newline='') as csvfile:
                    fieldnames = ['Time (s)', f'Speed ({self.display_unit})', 'Timestamp']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for data in self.graph_data:
                        writer.writerow({'Time (s)': data['Time'],
                                         f'Speed ({self.display_unit})': data['Speed'],
                                         'Timestamp': data['Timestamp']})
                messagebox.showinfo("Data Saved", f"Data saved to {filepath}")
                print(f"Data saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data:\n{e}")
            print(f"Failed to save data: {e}")
            traceback.print_exc()

    def convert_speed(self, speed_value):
        try:
            if self.display_unit == "km/h":
                speed_display = speed_value * 3.6
                unit = "km/h"
            elif self.display_unit == "mph":
                speed_display = speed_value * 2.23694
                unit = "mph"
            else:
                speed_display = speed_value
                unit = "m/s"
            return speed_display, unit
        except Exception as e:
            print(f"Exception in convert_speed: {e}")
            traceback.print_exc()
            return speed_value, "m/s"

    def is_float(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def on_closing(self):
        try:
            self.running = False
            if self.serial_connection:
                self.serial_connection.close()
            self.root.destroy()
        except Exception as e:
            print(f"Exception in on_closing: {e}")
            traceback.print_exc()

    def save_settings(self):
        try:
            # Implement the logic to save the current settings to the radar
            self.send_command("A!")  # Correct command to save settings
            messagebox.showinfo("Save Settings", "Settings saved to radar.")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings:\n{e}")
            print(f"Exception in save_settings: {e}")
            traceback.print_exc()

    def reset_settings(self):
        try:
            # Implement the logic to reset the radar settings
            self.send_command("P!")  # Correct command to reset settings
            messagebox.showinfo("Reset Settings", "Radar settings reset.")
        except Exception as e:
            messagebox.showerror("Reset Error", f"Failed to reset settings:\n{e}")
            print(f"Exception in reset_settings: {e}")
            traceback.print_exc()

# Create the main window and run the GUI
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = OPS243GUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        print(f"Exception in main: {e}")
        traceback.print_exc()