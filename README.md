# OPS243-A Radar Sensor GUI

## Description
This Python application provides a graphical user interface (GUI) for interacting with the OPS243-A radar sensor. The GUI enables users to control the sensor, visualize real-time speed and direction data, and configure various sensor parameters.

The application is built with the Tkinter library and communicates with the OPS243-A sensor over a serial connection.

---

## Features
- **Live Stats**: Displays current speed, direction, maximum speed, minimum speed, and average speed (over 5 seconds).
- **Unit Selection**: Supports speed display in kilometers per hour (km/h), miles per hour (mph), or meters per second (m/s).
- **Sensor Controls**:
  - Adjust frequency settings.
  - Configure output format (Speed, FFT, or Raw ADC).
  - Set magnitude and direction filters.
  - Switch between active and idle power modes.
- **Command Interface**: Allows manual command input for advanced users.
- **CLI Output**: Displays sensor responses in real-time.

---

## Requirements
- Python 3.6 or higher
- Required Python libraries:
  - `tkinter`
  - `serial` (Install with `pip install pyserial`)
  - `collections`
  - `time`
- OPS243-A radar sensor
- Serial connection to the sensor

---

## Installation
1. Clone the repository or download the source code:
   ```bash
   git clone https://github.com/ArianShamaeiSMU/OPS243-A_GUI.git
   cd OPS243-A_GUI
