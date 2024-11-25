
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
   ```
2. Install dependencies:
   ```bash
   pip install pyserial
   ```

---

## Usage
1. **Connect the Sensor**:
   - Connect the OPS243-A sensor to your computer via a serial port.
   - Update the `SERIAL_PORT` variable in the script to match your device's serial port (e.g., `/dev/tty.usbmodem1101` for macOS or `COM3` for Windows).

2. **Run the Application**:
   ```bash
   python ops243_gui.py
   ```

3. **Use the GUI**:
   - View real-time stats in the **Live Stats** section.
   - Configure sensor settings in the **Sensor Controls** section.
   - Send manual commands in the **Command Interface** section.

4. **Close the Application**:
   - Click the close button (X) in the GUI window. This ensures the serial connection is closed gracefully.

---

## GUI Overview
- **General Information**: Displays the connection status of the radar sensor.
- **Live Stats**: Provides real-time speed, direction, and calculated stats.
- **Sensor Controls**: Adjust key sensor settings such as frequency, output format, and filters.
- **Command Interface**: Enter manual commands directly.
- **Sensor Responses**: View responses from the sensor for debugging and verification.

---

## Configuration
- **Display Unit**:
  - Default: `km/h`
  - Change to `mph` or `m/s` using the radio buttons in the **Live Stats** section.
- **Frequency Control**:
  - Valid range: `-2` to `2`
  - Adjust via the entry box and "Set Frequency" button in the **Sensor Controls** section.
- **Output Format**:
  - Options: `Speed`, `FFT`, `Raw`
  - Adjust via the radio buttons in the **Sensor Controls** section.
- **Direction Filter**:
  - Options: `Both`, `Approaching`, `Receding`
- **Power Mode**:
  - Options: `Active`, `Idle`

---

## Troubleshooting
- **Failed to Connect**:
  - Verify the correct serial port in the `SERIAL_PORT` variable.
  - Ensure the OPS243-A sensor is powered on and connected properly.
- **No Data Received**:
  - Check the baud rate (`BAUD_RATE = 9600`) matches the sensor's settings.
- **Invalid Data**:
  - Ensure the sensor's output format is configured correctly.

---

## Notes
- The application assumes the OPS243-A sensor outputs speed data in a compatible format.
- For advanced usage, refer to the OPS243-A sensor documentation to modify commands and configurations.

---

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.
