import sys
import serial
import time
from serial.tools import list_ports
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QPushButton, QLabel,
                             QComboBox, QTextEdit, QFrame, QMessageBox,
                             QDialog, QLineEdit)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette
import pyqtgraph as pg

FAN_COLORS = {
    'Off': '#FFFFFF',  # White
    'Low': '#90EE90',  # Light Green
    'Medium': '#4CAF50',  # Medium Green
    'High': '#1B5E20'  # Dark Green
}


class PortSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Arduino Ports")
        layout = QVBoxLayout()

        # Fan Controller Selection
        fan_group = QGroupBox("Fan Controller")
        fan_layout = QVBoxLayout()

        # Dropdown for fan port
        fan_combo_layout = QHBoxLayout()
        fan_combo_layout.addWidget(QLabel("Select Port:"))
        self.fan_port_combo = QComboBox()
        fan_combo_layout.addWidget(self.fan_port_combo)
        fan_layout.addLayout(fan_combo_layout)

        # Manual entry for fan port
        fan_manual_layout = QHBoxLayout()
        fan_manual_layout.addWidget(QLabel("Manual Port:"))
        self.fan_port_manual = QLineEdit()
        self.fan_port_manual.setPlaceholderText("e.g., COM1 or /dev/ttyUSB0")
        fan_manual_layout.addWidget(self.fan_port_manual)
        fan_layout.addLayout(fan_manual_layout)

        fan_group.setLayout(fan_layout)
        layout.addWidget(fan_group)

        # Sensor Controller Selection
        sensor_group = QGroupBox("Sensor Controller")
        sensor_layout = QVBoxLayout()

        # Dropdown for sensor port
        sensor_combo_layout = QHBoxLayout()
        sensor_combo_layout.addWidget(QLabel("Select Port:"))
        self.sensor_port_combo = QComboBox()
        sensor_combo_layout.addWidget(self.sensor_port_combo)
        sensor_layout.addLayout(sensor_combo_layout)

        # Manual entry for sensor port
        sensor_manual_layout = QHBoxLayout()
        sensor_manual_layout.addWidget(QLabel("Manual Port:"))
        self.sensor_port_manual = QLineEdit()
        self.sensor_port_manual.setPlaceholderText("e.g., COM2 or /dev/ttyUSB1")
        sensor_manual_layout.addWidget(self.sensor_port_manual)
        sensor_layout.addLayout(sensor_manual_layout)

        sensor_group.setLayout(sensor_layout)
        layout.addWidget(sensor_group)

        # Baud rate selection
        baud_group = QGroupBox("Baud Rates")
        baud_layout = QHBoxLayout()

        # Fan controller baud
        fan_baud_layout = QVBoxLayout()
        fan_baud_layout.addWidget(QLabel("Fan Controller:"))
        self.fan_baud = QComboBox()
        self.fan_baud.addItems(['9600', '115200'])
        self.fan_baud.setCurrentText('9600')
        fan_baud_layout.addWidget(self.fan_baud)
        baud_layout.addLayout(fan_baud_layout)

        # Sensor controller baud
        sensor_baud_layout = QVBoxLayout()
        sensor_baud_layout.addWidget(QLabel("Sensor Controller:"))
        self.sensor_baud = QComboBox()
        self.sensor_baud.addItems(['9600', '115200'])
        self.sensor_baud.setCurrentText('115200')
        sensor_baud_layout.addWidget(self.sensor_baud)
        baud_layout.addLayout(sensor_baud_layout)

        baud_group.setLayout(baud_layout)
        layout.addWidget(baud_group)

        # Refresh button
        refresh_btn = QPushButton("Refresh Ports")
        refresh_btn.clicked.connect(self.refresh_ports)
        layout.addWidget(refresh_btn)

        # Help text
        help_text = QLabel(
            "Note: If your port is not listed, enter it manually.\n"
            "Common formats:\n"
            "- Windows: COM1, COM2, etc.\n"
            "- Linux: /dev/ttyUSB0, /dev/ttyACM0, etc.\n"
            "- Mac: /dev/tty.usbserial, /dev/tty.usbmodem, etc."
        )
        help_text.setStyleSheet("color: gray;")
        layout.addWidget(help_text)

        # OK/Cancel buttons
        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        self.setLayout(layout)
        self.refresh_ports()

class SensorArrayGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fan Array Control Interface v.0.02")
        self.setGeometry(100, 100, 1600, 1000)

        # Initialize serial connections as None
        self.fan_serial = None
        self.sensor_serial = None
        self.pattern_delay = 0.1

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Left panel for fan controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Fan Control Panel
        fan_panel = QFrame()
        fan_panel.setFrameStyle(QFrame.Panel | QFrame.Raised)
        fan_layout = QVBoxLayout(fan_panel)

        # Connection status and port selection
        connection_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect Devices")
        self.connect_btn.clicked.connect(self.show_port_selection)
        connection_layout.addWidget(self.connect_btn)

        # Fan array (4x4 grid of buttons)
        fan_grid = QGridLayout()
        self.fan_buttons = []
        for i in range(4):
            row = []
            for j in range(4):
                btn = QPushButton()
                btn.setCheckable(True)
                btn.setMinimumSize(50, 50)
                fan_num = i * 4 + j
                btn.clicked.connect(lambda checked, fan=fan_num: self.toggle_fan(fan))
                fan_grid.addWidget(btn, i, j)
                row.append(btn)
            self.fan_buttons.append(row)

        # Pattern timing control
        timing_layout = QHBoxLayout()
        timing_layout.addWidget(QLabel("Pattern Delay (s):"))
        self.pattern_delay_input = QLineEdit()
        self.pattern_delay_input.setText(str(self.pattern_delay))
        self.pattern_delay_input.textChanged.connect(self.update_pattern_delay)
        timing_layout.addWidget(self.pattern_delay_input)


        # Fan controls
        self.fan_mode = QComboBox()
        self.fan_mode.addItems(["Custom", "All Off", "All On", "Columns", "Rows", "Corners"])
        self.fan_mode.currentTextChanged.connect(self.change_fan_mode)

        speed_layout = QHBoxLayout()
        self.speed_select = QComboBox()
        self.speed_select.addItems(["Off", "Low", "Medium", "High"])
        speed_layout.addWidget(QLabel("Fan Speed:"))
        speed_layout.addWidget(self.speed_select)

        # Add all fan controls to panel
        fan_layout.addLayout(connection_layout)
        fan_layout.addWidget(QLabel("Fan Control Array"))
        fan_layout.addLayout(fan_grid)
        fan_layout.addWidget(QLabel("Patterns:"))
        fan_layout.addWidget(self.fan_mode)
        fan_layout.addLayout(speed_layout)

        # Add fan panel to left layout
        left_layout.addWidget(fan_panel)

        # Add log terminal
        self.log_terminal = QTextEdit()
        self.log_terminal.setReadOnly(True)
        self.log_terminal.setMaximumHeight(200)
        left_layout.addWidget(self.log_terminal)

        # Right panel for graphs
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Create graph widgets
        self.sensor_plots = []
        plot_grid = QGridLayout()
        for i in range(4):
            for j in range(4):
                plot_widget = pg.PlotWidget()
                plot_widget.setBackground('w')
                plot_widget.setTitle(f'Sensor {i * 4 + j + 1}')
                plot_widget.setLabel('left', 'Value')
                plot_widget.setLabel('bottom', 'Time (s)')
                plot_widget.showGrid(x=True, y=True)
                self.sensor_plots.append({
                    'widget': plot_widget,
                    'curve': plot_widget.plot(pen='b'),
                    'data': {'x': [], 'y': []}
                })
                plot_grid.addWidget(plot_widget, i, j)

        right_layout.addLayout(plot_grid)

        # Add panels to main layout
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(right_panel, stretch=2)

        # Setup sensor data collection timer
        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.update_sensor_data)
        self.sensor_timer.start(200)  # Update every 200ms

        # Initialize sensor data storage
        self.sensor_data = {i: {'times': [], 'values': []} for i in range(16)}
        self.start_time = time.time()

    def update_pattern_delay(self):
        try:
            new_delay = float(self.pattern_delay_input.text())
            if new_delay > 0:
                self.pattern_delay = new_delay
        except ValueError:
            pass

    def show_port_selection(self):
        """Show port selection dialog and connect to selected ports"""
        try:
            dialog = PortSelectionDialog(self)
            if dialog.exec_():
                fan_port, sensor_port, fan_baud, sensor_baud = dialog.get_selected_ports()
                if fan_port and sensor_port:  # Only connect if ports were selected
                    self.connect_devices(fan_port, sensor_port, fan_baud, sensor_baud)
        except Exception as e:
            self.log_terminal.append(f"Port selection error: {str(e)}")
            QMessageBox.warning(self, "Error", f"Port selection failed: {str(e)}")

    def connect_devices(self, fan_port, sensor_port, fan_baud=9600, sensor_baud=115200):
        """Connect to both fan and sensor controllers with specified baud rates"""
        # Close existing connections
        if self.fan_serial:
            try:
                self.fan_serial.close()
            except:
                pass
        if self.sensor_serial:
            try:
                self.sensor_serial.close()
            except:
                pass

        try:
            # Connect to fan controller
            if fan_port and fan_port != "No ports found":
                self.fan_serial = serial.Serial(fan_port, fan_baud, timeout=1)
                time.sleep(2)  # Wait for Arduino reset
                self.log_terminal.append(f"Connected to fan controller on {fan_port} at {fan_baud} baud")
            else:
                self.fan_serial = None
                self.log_terminal.append("No fan controller port selected")
        except Exception as e:
            self.log_terminal.append(f"Fan controller connection error: {str(e)}")
            self.fan_serial = None

        try:
            # Connect to sensor controller
            if sensor_port and sensor_port != "No ports found":
                self.sensor_serial = serial.Serial(sensor_port, sensor_baud, timeout=1)
                time.sleep(2)  # Wait for Arduino reset
                self.log_terminal.append(f"Connected to sensor controller on {sensor_port} at {sensor_baud} baud")
            else:
                self.sensor_serial = None
                self.log_terminal.append("No sensor controller port selected")
        except Exception as e:
            self.log_terminal.append(f"Sensor controller connection error: {str(e)}")
            self.sensor_serial = None
    def show_port_selection(self):
        """Show port selection dialog and connect to selected ports"""
        dialog = PortSelectionDialog(self)
        if dialog.exec_():
            fan_port, sensor_port, fan_baud, sensor_baud = dialog.get_selected_ports()
            self.connect_devices(fan_port, sensor_port, fan_baud, sensor_baud)
    def update_sensor_data(self):
        if not self.sensor_serial:
            return

        try:
            if self.sensor_serial.in_waiting:
                line = self.sensor_serial.readline().decode().strip()
                if line.startswith("START") and line.endswith("END"):
                    # Parse sensor data
                    parts = line.split(',')
                    timestamp = float(parts[1]) / 1000.0  # Convert to seconds

                    # Process each sensor reading
                    for i in range(16):
                        sensor_data = parts[2 + i].split(':')
                        if len(sensor_data) == 2:
                            value = float(sensor_data[1])
                            self.sensor_data[i]['times'].append(timestamp)
                            self.sensor_data[i]['values'].append(value)

                            # Keep only last 100 readings
                            if len(self.sensor_data[i]['times']) > 100:
                                self.sensor_data[i]['times'].pop(0)
                                self.sensor_data[i]['values'].pop(0)

                            # Update plot
                            self.sensor_plots[i]['curve'].setData(
                                self.sensor_data[i]['times'],
                                self.sensor_data[i]['values']
                            )
        except Exception as e:
            self.log_terminal.append(f"Sensor data error: {str(e)}")

    def update_fan_colors(self):
        if not hasattr(self, 'fan_states'):
            self.fan_states = [[0] * 4 for _ in range(4)]

        for i in range(4):
            for j in range(4):
                button = self.fan_buttons[i][j]
                if button.isChecked():
                    speed = self.speed_select.currentText()
                    button.setStyleSheet(f"background-color: {FAN_COLORS[speed]}")
                    self.fan_states[i][j] = list(FAN_COLORS.keys()).index(speed)
                else:
                    button.setStyleSheet(f"background-color: {FAN_COLORS['Off']}")
                    self.fan_states[i][j] = 0

    def toggle_fan(self, fan_num):
        if self.fan_serial:
            try:
                speed = self.speed_select.currentIndex()
                command = f"{fan_num},{speed}\n"
                self.fan_serial.write(command.encode())
                self.log_terminal.append(f"Fan {fan_num} set to speed {speed}")

                # Update button color
                row = fan_num // 4
                col = fan_num % 4
                button = self.fan_buttons[row][col]
                speed_text = self.speed_select.currentText()
                button.setStyleSheet(f"background-color: {FAN_COLORS[speed_text]}")

            except Exception as e:
                self.log_terminal.append(f"Fan control error: {str(e)}")
    def change_fan_mode(self, mode):
        if not self.fan_serial:
            return

        try:
            speed = self.speed_select.currentIndex()
            speed_text = self.speed_select.currentText()

            if mode == "All Off":
                for i in range(16):
                    self.fan_serial.write(f"{i},0\n".encode())
                    time.sleep(self.pattern_delay)
                    row, col = i // 4, i % 4
                    self.fan_buttons[row][col].setStyleSheet(f"background-color: {FAN_COLORS['Off']}")

            elif mode == "All On":
                for i in range(16):
                    self.fan_serial.write(f"{i},{speed}\n".encode())
                    time.sleep(self.pattern_delay)
                    row, col = i // 4, i % 4
                    self.fan_buttons[row][col].setStyleSheet(f"background-color: {FAN_COLORS[speed_text]}")

            elif mode == "Columns":
                for col in range(4):
                    for row in range(4):
                        fan_num = row * 4 + col
                        self.fan_serial.write(f"{fan_num},{speed}\n".encode())
                        time.sleep(self.pattern_delay)
                        self.fan_buttons[row][col].setStyleSheet(f"background-color: {FAN_COLORS[speed_text]}")

            elif mode == "Rows":
                for row in range(4):
                    for col in range(4):
                        fan_num = row * 4 + col
                        self.fan_serial.write(f"{fan_num},{speed}\n".encode())
                        time.sleep(self.pattern_delay)
                        self.fan_buttons[row][col].setStyleSheet(f"background-color: {FAN_COLORS[speed_text]}")

            elif mode == "Corners":
                corner_fans = [(0, 0), (0, 3), (3, 0), (3, 3)]
                for row, col in corner_fans:
                    fan_num = row * 4 + col
                    self.fan_serial.write(f"{fan_num},{speed}\n".encode())
                    time.sleep(self.pattern_delay)
                    self.fan_buttons[row][col].setStyleSheet(f"background-color: {FAN_COLORS[speed_text]}")

        except Exception as e:
            self.log_terminal.append(f"Fan mode error: {str(e)}")

    def closeEvent(self, event):
        if self.fan_serial:
            try:
                # Turn all fans off before closing
                for i in range(16):
                    self.fan_serial.write(f"{i},0\n".encode())
                self.fan_serial.close()
            except:
                pass

        if self.sensor_serial:
            try:
                self.sensor_serial.close()
            except:
                pass

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set dark theme
    app.setStyle('Fusion')

    window = SensorArrayGUI()
    window.show()
    sys.exit(app.exec_())
