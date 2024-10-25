import sys
import serial
import time
from serial.tools import list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QComboBox,
                             QTextEdit, QGroupBox, QCheckBox)
from PyQt5.QtCore import QTimer


class SerialCommandMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controller Command Monitor")
        self.setGeometry(100, 100, 1000, 800)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Port selection group
        port_group = QGroupBox("Serial Connection")
        port_layout = QHBoxLayout()

        self.port_combo = QComboBox()
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '115200'])
        self.refresh_btn = QPushButton("Refresh Ports")
        self.connect_btn = QPushButton("Connect")

        port_layout.addWidget(QLabel("Port:"))
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(QLabel("Baud:"))
        port_layout.addWidget(self.baud_combo)
        port_layout.addWidget(self.refresh_btn)
        port_layout.addWidget(self.connect_btn)

        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.connect_btn.clicked.connect(self.toggle_connection)

        port_group.setLayout(port_layout)
        layout.addWidget(port_group)

        # Monitoring options
        options_group = QGroupBox("Monitoring Options")
        options_layout = QHBoxLayout()

        self.show_timestamps = QCheckBox("Show Timestamps")
        self.show_timestamps.setChecked(True)
        self.show_hex = QCheckBox("Show Hex Values")
        self.auto_scroll = QCheckBox("Auto Scroll")
        self.auto_scroll.setChecked(True)

        options_layout.addWidget(self.show_timestamps)
        options_layout.addWidget(self.show_hex)
        options_layout.addWidget(self.auto_scroll)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Command monitoring
        monitor_group = QGroupBox("Command Monitor")
        monitor_layout = QVBoxLayout()

        # Fan commands
        self.fan_terminal = QTextEdit()
        self.fan_terminal.setReadOnly(True)
        fan_label = QLabel("Fan Control Commands:")
        monitor_layout.addWidget(fan_label)
        monitor_layout.addWidget(self.fan_terminal)

        # Sprayer commands
        self.sprayer_terminal = QTextEdit()
        self.sprayer_terminal.setReadOnly(True)
        sprayer_label = QLabel("Sprayer Control Commands:")
        monitor_layout.addWidget(sprayer_label)
        monitor_layout.addWidget(self.sprayer_terminal)

        # Raw data
        self.raw_terminal = QTextEdit()
        self.raw_terminal.setReadOnly(True)
        raw_label = QLabel("Raw Serial Data:")
        monitor_layout.addWidget(raw_label)
        monitor_layout.addWidget(self.raw_terminal)

        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)

        # Clear buttons
        clear_layout = QHBoxLayout()
        clear_fan_btn = QPushButton("Clear Fan Log")
        clear_sprayer_btn = QPushButton("Clear Sprayer Log")
        clear_raw_btn = QPushButton("Clear Raw Log")
        clear_fan_btn.clicked.connect(self.fan_terminal.clear)
        clear_sprayer_btn.clicked.connect(self.sprayer_terminal.clear)
        clear_raw_btn.clicked.connect(self.raw_terminal.clear)

        clear_layout.addWidget(clear_fan_btn)
        clear_layout.addWidget(clear_sprayer_btn)
        clear_layout.addWidget(clear_raw_btn)
        layout.addLayout(clear_layout)

        # Initialize serial port and timer
        self.serial_port = None
        self.read_timer = QTimer()
        self.read_timer.timeout.connect(self.read_serial)
        self.read_timer.start(10)  # Check every 10ms

        # Command parsing state
        self.current_command = ""

        # Initial port refresh
        self.refresh_ports()

        # Statistics
        self.fan_commands = 0
        self.sprayer_commands = 0
        self.total_commands = 0

        # Status bar
        self.statusBar().showMessage("Ready")

    def refresh_ports(self):
        """Refresh available serial ports"""
        self.port_combo.clear()
        ports = [port.device for port in list_ports.comports()]
        self.port_combo.addItems(ports)
        self.update_status(f"Found {len(ports)} ports")

    def toggle_connection(self):
        """Connect to or disconnect from the serial port"""
        if self.serial_port is None:
            try:
                port = self.port_combo.currentText()
                baud = int(self.baud_combo.currentText())
                self.serial_port = serial.Serial(port, baud, timeout=0)
                self.connect_btn.setText("Disconnect")
                self.update_status(f"Connected to {port} at {baud} baud")
            except Exception as e:
                self.update_status(f"Connection error: {str(e)}")
        else:
            try:
                self.serial_port.close()
                self.serial_port = None
                self.connect_btn.setText("Connect")
                self.update_status("Disconnected")
            except Exception as e:
                self.update_status(f"Disconnection error: {str(e)}")

    def read_serial(self):
        """Read and process serial data"""
        if not self.serial_port or not self.serial_port.is_open:
            return

        try:
            if self.serial_port.in_waiting:
                data = self.serial_port.read(self.serial_port.in_waiting).decode()
                self.current_command += data

                # Process complete commands
                while '\n' in self.current_command:
                    command, self.current_command = self.current_command.split('\n', 1)
                    self.process_command(command.strip())

        except Exception as e:
            self.update_status(f"Read error: {str(e)}")

    def process_command(self, command):
        """Process and categorize commands"""
        timestamp = f"[{time.strftime('%H:%M:%S.%f')[:-3]}] " if self.show_timestamps.isChecked() else ""
        hex_data = f" (HEX: {' '.join([hex(ord(c))[2:].upper() for c in command])})" if self.show_hex.isChecked() else ""

        # Log raw data
        self.raw_terminal.append(f"{timestamp}RAW: {command}{hex_data}")

        # Parse and categorize command
        if ',' in command:
            parts = command.split(',')

            # Fan control command (format: "fan_number,speed")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                fan_num = int(parts[0])
                speed = int(parts[1])
                if 0 <= fan_num <= 15 and 0 <= speed <= 4:
                    self.fan_commands += 1
                    speed_text = ["Off", "Very Low", "Low", "Medium", "High"][speed]
                    self.fan_terminal.append(f"{timestamp}Fan {fan_num} set to {speed_text}{hex_data}")

            # Sprayer pattern command (format: "PATTERN,binary_pattern" or "CYCLE,duration")
            elif parts[0] in ["PATTERN", "CYCLE"]:
                self.sprayer_commands += 1
                if parts[0] == "PATTERN":
                    self.sprayer_terminal.append(f"{timestamp}New spray pattern: {parts[1]}{hex_data}")
                else:
                    self.sprayer_terminal.append(f"{timestamp}Cycle duration set to {parts[1]}ms{hex_data}")

        # Stop command
        elif command == "STOP":
            self.sprayer_commands += 1
            self.sprayer_terminal.append(f"{timestamp}Stop command received{hex_data}")

        self.total_commands += 1
        self.update_status(
            f"Total commands: {self.total_commands} (Fan: {self.fan_commands}, Sprayer: {self.sprayer_commands})")

        # Auto-scroll if enabled
        if self.auto_scroll.isChecked():
            self.fan_terminal.verticalScrollBar().setValue(
                self.fan_terminal.verticalScrollBar().maximum())
            self.sprayer_terminal.verticalScrollBar().setValue(
                self.sprayer_terminal.verticalScrollBar().maximum())
            self.raw_terminal.verticalScrollBar().setValue(
                self.raw_terminal.verticalScrollBar().maximum())

    def update_status(self, message):
        """Update status bar with message"""
        self.statusBar().showMessage(message)

    def closeEvent(self, event):
        """Clean up on close"""
        if self.serial_port:
            self.serial_port.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = SerialCommandMonitor()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()