import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QComboBox,
                             QTextEdit, QSpinBox, QGridLayout, QFrame)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor, QPalette


class SensorPortDisplay(QFrame):
    def __init__(self, port_num):
        super().__init__()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        layout = QVBoxLayout()

        # Port title
        title = QLabel(f"Analog Port A{port_num}")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        # Current value
        self.value_label = QLabel("Current: ---")
        layout.addWidget(self.value_label)

        # Min/Max values
        self.min_max_label = QLabel("Min: --- Max: ---")
        layout.addWidget(self.min_max_label)

        # Change indicator
        self.change_label = QLabel("Change: ---")
        layout.addWidget(self.change_label)

        # Activity indicator
        self.activity_indicator = QLabel("■")
        self.activity_indicator.setStyleSheet("color: gray;")
        layout.addWidget(self.activity_indicator)

        self.setLayout(layout)

    def update_values(self, current, min_val, max_val, change):
        self.value_label.setText(f"Current: {current}")
        self.min_max_label.setText(f"Min: {min_val} Max: {max_val}")
        self.change_label.setText(f"Change: {change}")

        # Update activity indicator based on change
        if change > 10:
            self.activity_indicator.setStyleSheet("color: green;")
        elif change > 5:
            self.activity_indicator.setStyleSheet("color: yellow;")
        else:
            self.activity_indicator.setStyleSheet("color: gray;")


class SensorDebugTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arduino Sensor Port Diagnostic Tool")
        self.setGeometry(100, 100, 1000, 600)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Connection controls
        conn_layout = QHBoxLayout()

        self.port_combo = QComboBox()
        self.refresh_ports()
        conn_layout.addWidget(QLabel("Port:"))
        conn_layout.addWidget(self.port_combo)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '115200'])
        self.baud_combo.setCurrentText('9600')
        conn_layout.addWidget(QLabel("Baud:"))
        conn_layout.addWidget(self.baud_combo)

        self.refresh_btn = QPushButton("Refresh Ports")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.refresh_btn)
        conn_layout.addWidget(self.connect_btn)

        layout.addLayout(conn_layout)

        # Sensor displays
        sensor_grid = QGridLayout()
        self.sensor_displays = []
        for i in range(6):  # A0 through A5
            display = SensorPortDisplay(i)
            row = i // 3
            col = i % 3
            sensor_grid.addWidget(display, row, col)
            self.sensor_displays.append(display)

        layout.addLayout(sensor_grid)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(200)
        layout.addWidget(QLabel("Debug Log:"))
        layout.addWidget(self.log_display)

        # Raw data display
        self.raw_display = QTextEdit()
        self.raw_display.setReadOnly(True)
        self.raw_display.setMaximumHeight(100)
        layout.addWidget(QLabel("Raw Data:"))
        layout.addWidget(self.raw_display)

        # Initialize serial and timer
        self.serial = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_sensor)
        self.timer.start(100)  # 100ms update rate

        self.log("Diagnostic tool started")

    def refresh_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if ports:
            self.port_combo.addItems(ports)
        else:
            self.port_combo.addItem("No ports found")

    def toggle_connection(self):
        if self.serial is None:
            try:
                port = "/tmp/tty.virtual1"
                baud = int(self.baud_combo.currentText())

                self.serial = serial.Serial(port, baud, timeout=0.1)
                self.connect_btn.setText("Disconnect")
                self.log(f"Connected to {port} at {baud} baud")

            except Exception as e:
                self.log(f"Connection error: {str(e)}")
                self.serial = None
        else:
            self.serial.close()
            self.serial = None
            self.connect_btn.setText("Connect")
            self.log("Disconnected")

    def read_sensor(self):
        if not self.serial:
            return

        try:
            if self.serial.in_waiting:
                line = self.serial.readline().decode().strip()
                self.raw_display.append(line)

                if line == "START":
                    return

                if line == "END":
                    return

                if ":" in line:
                    # Parse: PORT:CURRENT:MIN:MAX:CHANGE
                    parts = line.split(":")
                    if len(parts) == 5:
                        port = int(parts[0][1])  # Remove 'A' from port name
                        current = int(parts[1])
                        min_val = int(parts[2])
                        max_val = int(parts[3])
                        change = int(parts[4])

                        if 0 <= port < len(self.sensor_displays):
                            self.sensor_displays[port].update_values(
                                current, min_val, max_val, change)

        except Exception as e:
            self.log(f"Read error: {str(e)}")

    def log(self, message):
        self.log_display.append(f"{message}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SensorDebugTool()
    window.show()
    sys.exit(app.exec_())