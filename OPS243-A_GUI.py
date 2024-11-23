import tkinter as tk
from tkinter import messagebox
import serial
import time
from collections import deque

# Set up the serial connection (adjust port and baud rate as needed)
SERIAL_PORT = '/dev/tty.usbmodem1101'
BAUD_RATE = 9600

class OPS243GUI:
    def __init__(self, root):
        print("Initializing OPS243GUI...")
        self.root = root
        self.root.title("OPS243-A Radar Sensor")
        self.root.resizable(False, False)
        self.serial_connection = None

        # Initialize data variables
        self.speed_value = 0.0
        self.direction_value = "N/A"
        self.max_speed = None
        self.min_speed = None
        self.speed_values = deque()
        self.start_time = time.time()
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

        # UI Elements
        self.create_widgets()

        # Connect to the sensor
        self.connect_to_sensor()

    def create_widgets(self):
        # Frames
        self.info_frame = tk.LabelFrame(self.root, text="General Information", padx=10, pady=10)
        self.info_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.stats_frame = tk.LabelFrame(self.root, text="Live Stats", padx=10, pady=10)
        self.stats_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.control_frame = tk.LabelFrame(self.root, text="Sensor Controls", padx=10, pady=10)
        self.control_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.command_frame = tk.LabelFrame(self.root, text="Command Interface", padx=10, pady=10)
        self.command_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        # Info Labels
        self.info_text = tk.StringVar(value="Connecting to sensor...")
        self.info_label = tk.Label(self.info_frame, textvariable=self.info_text, justify="left", width=60, anchor="w")
        self.info_label.pack(anchor="w")

        # Stats Labels
        self.speed_text = tk.StringVar(value="Speed: N/A")
        self.max_speed_text = tk.StringVar(value="Max Speed: N/A")
        self.min_speed_text = tk.StringVar(value="Min Speed: N/A")
        self.avg_speed_text = tk.StringVar(value="Avg Speed (5s): N/A")
        self.direction_text = tk.StringVar(value="Direction: N/A")

        tk.Label(self.stats_frame, textvariable=self.speed_text, anchor="w", width=60).pack(anchor="w")
        tk.Label(self.stats_frame, textvariable=self.max_speed_text, anchor="w", width=60).pack(anchor="w")
        tk.Label(self.stats_frame, textvariable=self.min_speed_text, anchor="w", width=60).pack(anchor="w")
        tk.Label(self.stats_frame, textvariable=self.avg_speed_text, anchor="w", width=60).pack(anchor="w")
        tk.Label(self.stats_frame, textvariable=self.direction_text, anchor="w", width=60).pack(anchor="w")

        # Unit Toggle
        self.unit_var = tk.StringVar(value=self.display_unit)
        unit_frame = tk.Frame(self.stats_frame)
        unit_frame.pack(anchor="w")
        tk.Label(unit_frame, text="Display Unit: ").pack(side="left")
        tk.Radiobutton(unit_frame, text="km/h", variable=self.unit_var, value="km/h", command=self.update_unit).pack(side="left")
        tk.Radiobutton(unit_frame, text="mph", variable=self.unit_var, value="mph", command=self.update_unit).pack(side="left")
        tk.Radiobutton(unit_frame, text="m/s", variable=self.unit_var, value="m/s", command=self.update_unit).pack(side="left")

        # Sensor Controls
        # Frequency Control
        freq_frame = tk.Frame(self.control_frame)
        freq_frame.pack(anchor="w", pady=5)
        tk.Label(freq_frame, text="Frequency Control (T=n): ").pack(side="left")
        self.freq_var = tk.IntVar(value=self.frequency)
        self.freq_entry = tk.Entry(freq_frame, textvariable=self.freq_var, width=5)
        self.freq_entry.pack(side="left")
        tk.Button(freq_frame, text="Set Frequency", command=self.set_frequency).pack(side="left", padx=5)

        # Output Format Control
        output_frame = tk.Frame(self.control_frame)
        output_frame.pack(anchor="w", pady=5)
        tk.Label(output_frame, text="Output Format: ").pack(side="left")
        self.output_var = tk.StringVar(value="Speed")
        tk.Radiobutton(output_frame, text="Speed", variable=self.output_var, value="Speed", command=self.set_output_format).pack(side="left")
        tk.Radiobutton(output_frame, text="FFT Output", variable=self.output_var, value="FFT", command=self.set_output_format).pack(side="left")
        tk.Radiobutton(output_frame, text="Raw ADC", variable=self.output_var, value="Raw", command=self.set_output_format).pack(side="left")

        # Magnitude Filter Control
        mag_frame = tk.Frame(self.control_frame)
        mag_frame.pack(anchor="w", pady=5)
        tk.Label(mag_frame, text="Magnitude Filter (M>n): ").pack(side="left")
        self.mag_var = tk.IntVar(value=self.magnitude_filter)
        self.mag_entry = tk.Entry(mag_frame, textvariable=self.mag_var, width=5)
        self.mag_entry.pack(side="left")
        tk.Button(mag_frame, text="Set Magnitude Filter", command=self.set_magnitude_filter).pack(side="left", padx=5)

        # Direction Filter Control
        dir_frame = tk.Frame(self.control_frame)
        dir_frame.pack(anchor="w", pady=5)
        tk.Label(dir_frame, text="Direction Filter: ").pack(side="left")
        self.dir_var = tk.StringVar(value=self.direction_filter)
        tk.Radiobutton(dir_frame, text="Both", variable=self.dir_var, value="Both", command=self.set_direction_filter).pack(side="left")
        tk.Radiobutton(dir_frame, text="Approaching", variable=self.dir_var, value="Approaching", command=self.set_direction_filter).pack(side="left")
        tk.Radiobutton(dir_frame, text="Receding", variable=self.dir_var, value="Receding", command=self.set_direction_filter).pack(side="left")

        # Power Mode Control
        power_frame = tk.Frame(self.control_frame)
        power_frame.pack(anchor="w", pady=5)
        tk.Label(power_frame, text="Power Mode: ").pack(side="left")
        self.power_var = tk.StringVar(value=self.power_mode)
        tk.Radiobutton(power_frame, text="Active", variable=self.power_var, value="Active", command=self.set_power_mode).pack(side="left")
        tk.Radiobutton(power_frame, text="Idle", variable=self.power_var, value="Idle", command=self.set_power_mode).pack(side="left")

        # Command Interface
        self.command_entry = tk.Entry(self.command_frame, width=50)
        self.command_entry.pack(side="left", padx=5)
        self.command_entry.bind('<Return>', self.send_user_command)
        self.send_button = tk.Button(self.command_frame, text="Send", command=self.send_user_command)
        self.send_button.pack(side="left", padx=5)

        # CLI Output
        self.cli_frame = tk.LabelFrame(self.root, text="Sensor Responses", padx=10, pady=10)
        self.cli_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        self.cli_text = tk.Text(self.cli_frame, height=10, width=80, state='disabled')
        self.cli_text.pack()

    def update_unit(self):
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
        self.update_gui()

    def set_frequency(self):
        freq_value = self.freq_var.get()
        if freq_value >= -2 and freq_value <= 2:
            command = f"T={freq_value}"
            self.send_command(command)
            self.frequency = freq_value
            print(f"Frequency set to T={freq_value}")
        else:
            messagebox.showerror("Invalid Frequency", "Frequency must be between -2 and 2.")

    def set_output_format(self):
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

    def set_magnitude_filter(self):
        mag_value = self.mag_var.get()
        command = f"M>{mag_value}"
        self.send_command(command)
        self.magnitude_filter = mag_value
        print(f"Magnitude filter set to M>{mag_value}")

    def set_direction_filter(self):
        direction = self.dir_var.get()
        if direction == "Both":
            self.send_command("R|")
        elif direction == "Approaching":
            self.send_command("R+")
        elif direction == "Receding":
            self.send_command("R-")
        self.direction_filter = direction
        print(f"Direction filter set to {direction}")

    def set_power_mode(self):
        power_mode = self.power_var.get()
        if power_mode == "Active":
            self.send_command("PA")
        elif power_mode == "Idle":
            self.send_command("PI")
        self.power_mode = power_mode
        print(f"Power mode set to {power_mode}")

    def send_user_command(self, event=None):
        command = self.command_entry.get()
        if command and self.serial_connection:
            self.send_command(command)
            self.command_entry.delete(0, 'end')

    def connect_to_sensor(self):
        try:
            print("Attempting to connect to sensor...")
            self.serial_connection = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)  # Set timeout to 0.1 seconds
            time.sleep(2)  # Allow time for the connection to establish
            self.info_text.set("Connected to OPS243-A sensor.")
            print("Sensor connected.")
            # Configure the sensor
            self.configure_sensor()
            # Start updates using root.after
            self.running = True
            self.update_stats()
            self.calculate_avg_speed()
        except serial.SerialException as e:
            messagebox.showerror("Connection Error", f"Failed to connect to sensor:\n{e}")
            self.info_text.set("Failed to connect to sensor.")
            print(f"Failed to connect to sensor: {e}")
            # Ensure updates do not run without sensor connection
            self.running = False

    def configure_sensor(self):
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

    def send_command(self, command):
        full_command = f"{command}\n".encode('utf-8')
        self.serial_connection.write(full_command)
        time.sleep(0.05)  # Short delay
        # Read acknowledgment
        ack = self.serial_connection.readline().decode('utf-8').strip()
        response = f"Sent: {command}\nReceived: {ack}\n"
        print(response)
        # Schedule GUI update in the main thread
        self.update_cli(response)

    def update_cli(self, message):
        self.cli_text.configure(state='normal')
        self.cli_text.insert('end', message)
        self.cli_text.configure(state='disabled')
        self.cli_text.see('end')  # Scroll to the end

    def update_stats(self):
        if self.running and self.serial_connection:
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
                    if self.display_unit == "km/h":
                        speed_display = speed_value * 3.6
                        unit = "km/h"
                        max_speed_display = self.max_speed * 3.6
                        min_speed_display = self.min_speed * 3.6
                    elif self.display_unit == "mph":
                        speed_display = speed_value * 2.23694
                        unit = "mph"
                        max_speed_display = self.max_speed * 2.23694
                        min_speed_display = self.min_speed * 2.23694
                    else:
                        speed_display = speed_value
                        unit = "m/s"
                        max_speed_display = self.max_speed
                        min_speed_display = self.min_speed

                    self.speed_text_value = f"Speed: {speed_display:.2f} {unit}"
                    self.max_speed_text_value = f"Max Speed: {max_speed_display:.2f} {unit}"
                    self.min_speed_text_value = f"Min Speed: {min_speed_display:.2f} {unit}"

                    # Update the GUI labels
                    self.update_gui()
                else:
                    # Invalid data received; skip updating the GUI
                    if data_line:
                        print(f"Invalid data received: '{data_line}'")
                        self.update_cli(f"Invalid data: {data_line}\n")
                    pass  # Retain previous values

            except Exception as e:
                # Log the exception if needed
                print(f"Error in update_stats: {e}")
                self.update_cli(f"Error: {e}\n")
                pass  # Retain previous values

        # Schedule next update in 100 ms (0.1 seconds)
        self.root.after(100, self.update_stats)

    def calculate_avg_speed(self):
        if self.running:
            current_time = time.time()
            # Remove speed entries older than 5 seconds
            while self.speed_values and (current_time - self.speed_values[0][0]) > 5:
                self.speed_values.popleft()
            # Calculate average speed
            if self.speed_values:
                avg_speed = sum(speed for _, speed in self.speed_values) / len(self.speed_values)
                if self.display_unit == "km/h":
                    avg_speed_display = avg_speed * 3.6
                    unit = "km/h"
                elif self.display_unit == "mph":
                    avg_speed_display = avg_speed * 2.23694
                    unit = "mph"
                else:
                    avg_speed_display = avg_speed
                    unit = "m/s"
                self.avg_speed_text_value = f"Avg Speed (5s): {avg_speed_display:.2f} {unit}"
            else:
                self.avg_speed_text_value = "Avg Speed (5s): N/A"
            # Update the GUI label
            self.update_avg_speed_gui()

        # Schedule next update in 1000 ms (1 second)
        self.root.after(1000, self.calculate_avg_speed)

    def update_gui(self):
        self.speed_text.set(self.speed_text_value)
        self.max_speed_text.set(self.max_speed_text_value)
        self.min_speed_text.set(self.min_speed_text_value)
        self.direction_text.set(f"Direction: {self.direction_value}")

    def update_avg_speed_gui(self):
        self.avg_speed_text.set(self.avg_speed_text_value)

    def is_float(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def on_closing(self):
        self.running = False
        if self.serial_connection:
            self.serial_connection.close()
        self.root.destroy()

# Create the main window and run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = OPS243GUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()