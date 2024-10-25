import sys
import time
from serial.tools import list_ports
import serial
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QTextEdit, QLabel, QComboBox,
                             QMessageBox, QLineEdit, QHBoxLayout, QCheckBox)
from PyQt5.QtCore import QTimer


class SerialPortTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Serial Port Tester")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Port selection section
        port_section = QWidget()
        port_layout = QHBoxLayout(port_section)

        # Port selection
        port_left = QVBoxLayout()
        self.port_combo = QComboBox()
        port_left.addWidget(QLabel("Available Ports:"))
        port_left.addWidget(self.port_combo)

        # Manual port entry
        port_right = QVBoxLayout()
        self.manual_port = QLineEdit()
        self.manual_port.setPlaceholderText("Enter port manually (e.g., COM1 or /dev/ttyS0)")
        port_right.addWidget(QLabel("Manual Port Entry:"))
        port_right.addWidget(self.manual_port)

        port_layout.addLayout(port_left)
        port_layout.addLayout(port_right)
        layout.addWidget(port_section)

        # Refresh and connect buttons
        button_layout = QHBoxLayout()

        # Refresh ports button
        refresh_btn = QPushButton("Refresh Ports")
        refresh_btn.clicked.connect(self.refresh_ports)
        button_layout.addWidget(refresh_btn)

        # Connect buttons
        self.connect_btn = QPushButton("Connect to Selected")
        self.connect_btn.clicked.connect(lambda: self.connect_port(False))
        button_layout.addWidget(self.connect_btn)

        self.connect_manual_btn = QPushButton("Connect to Manual")
        self.connect_manual_btn.clicked.connect(lambda: self.connect_port(True))
        button_layout.addWidget(self.connect_manual_btn)

        layout.addLayout(button_layout)

        # Status section
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(QLabel("Connection Status:"))
        layout.addWidget(self.status_text)

        # Test controls
        test_layout = QHBoxLayout()

        self.loopback_btn = QPushButton("Run Loopback Test")
        self.loopback_btn.clicked.connect(self.run_loopback_test)
        test_layout.addWidget(self.loopback_btn)

        self.continuous_cb = QCheckBox("Continuous Send")
        test_layout.addWidget(self.continuous_cb)

        layout.addLayout(test_layout)

        # Terminal
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        layout.addWidget(QLabel("Communication Log:"))
        layout.addWidget(self.terminal)

        # Initialize serial port
        self.serial_port = None
        self.read_timer = QTimer()
        self.read_timer.timeout.connect(self.read_serial)
        self.read_timer.start(100)

        # Continuous send timer
        self.send_timer = QTimer()
        self.send_timer.timeout.connect(lambda: self.run_loopback_test(True))

        # Initial port refresh
        self.refresh_ports()

    def refresh_ports(self):
        """Refresh the list of available ports with detailed information"""
        self.port_combo.clear()
        try:
            ports = list_ports.comports()
            self.terminal.append("=== Available Ports ===")

            if not ports:
                self.terminal.append("No ports found!")

            for port in ports:
                # Add to combo box
                self.port_combo.addItem(port.device)

                # Show detailed information
                port_info = (f"\nPort: {port.device}\n"
                             f"Description: {port.description}\n"
                             f"Hardware ID: {port.hwid}\n"
                             f"VID:PID: {port.vid}:{port.pid}\n"
                             f"Serial Number: {port.serial_number}\n"
                             f"Location: {port.location}\n"
                             f"Manufacturer: {port.manufacturer}\n"
                             f"Product: {port.product}\n"
                             f"Interface: {port.interface}\n")
                self.terminal.append(port_info)

            self.terminal.append("=" * 40 + "\n")

        except Exception as e:
            self.terminal.append(f"Error refreshing ports: {str(e)}")

    def connect_port(self, use_manual=False):
        """Connect to either selected or manually entered port"""
        if self.serial_port:
            try:
                self.serial_port.close()
                self.serial_port = None
                self.status_text.setText("Disconnected")
                self.connect_btn.setText("Connect to Selected")
                self.connect_manual_btn.setText("Connect to Manual")
                self.terminal.append("Disconnected from port")
                return
            except Exception as e:
                self.terminal.append(f"Error disconnecting: {str(e)}")
                return

        try:
            port = self.manual_port.text() if use_manual else self.port_combo.currentText()
            if not port:
                raise ValueError("No port specified")

            self.status_text.setText(f"Attempting to connect to {port}...")
            self.serial_port = serial.Serial(port, 115200, timeout=0.1)

            if self.serial_port.is_open:
                self.status_text.setText(f"Connected to {port}")
                self.connect_btn.setText("Disconnect")
                self.connect_manual_btn.setText("Disconnect")
                self.terminal.append(f"Successfully connected to {port}")
            else:
                raise ConnectionError("Failed to open port")

        except Exception as e:
            self.status_text.setText(f"Connection failed: {str(e)}")
            self.terminal.append(f"Connection error: {str(e)}")
            self.serial_port = None

    def read_serial(self):
        """Read data from serial port"""
        if self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.readline().decode()
                    self.terminal.append(f"RECEIVED: {data.strip()}")
            except Exception as e:
                self.terminal.append(f"Read error: {str(e)}")

    def run_loopback_test(self, continuous=False):
        """Send test data through the serial port"""
        if not self.serial_port or not self.serial_port.is_open:
            self.terminal.append("Not connected to any port")
            return

        try:
            # Send test message
            test_msg = f"TEST_{random.randint(1000, 9999)}\n"
            self.terminal.append(f"SENDING: {test_msg.strip()}")
            self.serial_port.write(test_msg.encode())

            if not continuous and self.continuous_cb.isChecked():
                self.send_timer.start(1000)  # Start continuous sending
            elif continuous and not self.continuous_cb.isChecked():
                self.send_timer.stop()  # Stop continuous sending

        except Exception as e:
            self.terminal.append(f"Send error: {str(e)}")
            self.send_timer.stop()


def main():
    app = QApplication(sys.argv)
    window = SerialPortTester()
    window.show()

    # Show instructions
    QMessageBox.information(window, "Virtual Port Setup",
                            "To use virtual ports:\n\n"
                            "1. Windows: Install COM0COM and create a pair\n"
                            "2. Linux/Mac: Run 'socat -d -d pty,raw,echo=0 pty,raw,echo=0'\n\n"
                            "Enter the port manually if it's not showing in the list.\n"
                            "Common formats:\n"
                            "- Windows: COM1, COM2, etc.\n"
                            "- Linux: /dev/ttyS0, /dev/pts/1, etc.\n"
                            "- Mac: /dev/tty.usbserial, /dev/pts/1, etc.")

    app.exec_()


if __name__ == "__main__":
    main()