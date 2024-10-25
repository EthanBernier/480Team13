import time
import random
import serial
from serial.tools import list_ports
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QComboBox,
                             QTextEdit, QTabWidget, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
import threading
import queue


class SerialMonitor:
    def __init__(self):
        self.running = False
        self.queue = queue.Queue()
        self.thread = None

    def start_monitoring(self, serial_port, callback):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_serial,
                                       args=(serial_port, callback))
        self.thread.daemon = True
        self.thread.start()

    def stop_monitoring(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _monitor_serial(self, serial_port, callback):
        while self.running:
            if serial_port.in_waiting:
                try:
                    data = serial_port.readline().decode().strip()
                    callback(data)
                except Exception as e:
                    callback(f"Error reading serial: {str(e)}")
            time.sleep(0.01)


class SensorDebugGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensor Array Debug Interface")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize serial monitor
        self.serial_monitor = SerialMonitor()

        # Initialize tester
        self.tester = SensorArrayTester(self)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Create control panel
        control_panel = QGroupBox("Control Panel")
        control_layout = QHBoxLayout()

        # Port selection
        port_layout = QVBoxLayout()
        self.port_combo = QComboBox()
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '115200'])
        self.baud_combo.setCurrentText('115200')
        self.refresh_btn = QPushButton("Refresh Ports")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_port)
        port_layout.addWidget(QLabel("Serial Port:"))
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(QLabel("Baud Rate:"))
        port_layout.addWidget(self.baud_combo)
        port_layout.addWidget(self.refresh_btn)
        port_layout.addWidget(self.connect_btn)
        control_layout.addLayout(port_layout)

        # Test data configuration
        test_config = QVBoxLayout()
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 3600)
        self.duration_spin.setValue(10)
        self.noise_spin = QDoubleSpinBox()
        self.noise_spin.setRange(0, 1)
        self.noise_spin.setSingleStep(0.1)
        self.noise_spin.setValue(0.1)

        # Add send interval control
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 5000)  # 100ms to 5000ms
        self.interval_spin.setValue(200)
        self.interval_spin.setSingleStep(100)

        test_config.addWidget(QLabel("Duration (s):"))
        test_config.addWidget(self.duration_spin)
        test_config.addWidget(QLabel("Noise Level:"))
        test_config.addWidget(self.noise_spin)
        test_config.addWidget(QLabel("Send Interval (ms):"))
        test_config.addWidget(self.interval_spin)
        control_layout.addLayout(test_config)

        # Debug options
        debug_options = QVBoxLayout()
        self.raw_data_cb = QCheckBox("Show Raw Data")
        self.parsed_data_cb = QCheckBox("Show Parsed Data")
        self.timing_cb = QCheckBox("Show Timing Info")
        self.echo_cb = QCheckBox("Show Serial Echo")
        debug_options.addWidget(QLabel("Debug Options:"))
        debug_options.addWidget(self.raw_data_cb)
        debug_options.addWidget(self.parsed_data_cb)
        debug_options.addWidget(self.timing_cb)
        debug_options.addWidget(self.echo_cb)
        control_layout.addLayout(debug_options)

        # Test control buttons
        button_layout = QVBoxLayout()
        self.generate_btn = QPushButton("Generate Test Data")
        self.generate_btn.clicked.connect(self.generate_data)
        self.visualize_btn = QPushButton("Visualize Data")
        self.visualize_btn.clicked.connect(self.visualize_data)
        self.send_btn = QPushButton("Send Test Data")
        self.send_btn.clicked.connect(self.send_data)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_test)
        self.stop_btn.setEnabled(False)

        # Add manual send button and text field
        self.manual_send_layout = QHBoxLayout()
        self.manual_text = QTextEdit()
        self.manual_text.setMaximumHeight(50)
        self.manual_send_btn = QPushButton("Send")
        self.manual_send_btn.clicked.connect(self.send_manual_data)
        self.manual_send_layout.addWidget(self.manual_text)
        self.manual_send_layout.addWidget(self.manual_send_btn)

        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.visualize_btn)
        button_layout.addWidget(self.send_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addLayout(self.manual_send_layout)
        control_layout.addLayout(button_layout)

        control_panel.setLayout(control_layout)
        main_layout.addWidget(control_panel)

        # Create tab widget for terminals
        self.terminals = QTabWidget()

        # Main debug terminal
        self.debug_terminal = QTextEdit()
        self.debug_terminal.setReadOnly(True)
        self.terminals.addTab(self.debug_terminal, "Debug Log")

        # Raw data terminal
        self.raw_terminal = QTextEdit()
        self.raw_terminal.setReadOnly(True)
        self.terminals.addTab(self.raw_terminal, "Raw Data")

        # Serial monitor terminal
        self.serial_terminal = QTextEdit()
        self.serial_terminal.setReadOnly(True)
        self.terminals.addTab(self.serial_terminal, "Serial Monitor")

        main_layout.addWidget(self.terminals)

        # Initialize
        self.refresh_ports()
        self.test_running = False

        # Setup timer for data sending
        self.send_timer = QTimer()
        self.send_timer.timeout.connect(self.send_next_data)
        self.current_sample = 0

    def send_manual_data(self):
        if not self.tester.serial_port:
            self.debug_terminal.append("Not connected to serial port")
            return

        try:
            data = self.manual_text.toPlainText() + '\n'
            self.tester.serial_port.write(data.encode())
            self.debug_terminal.append(f"Sent manual data: {data.strip()}")
            self.manual_text.clear()
        except Exception as e:
            self.debug_terminal.append(f"Error sending manual data: {str(e)}")

    def refresh_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in list_ports.comports()]
        self.port_combo.addItems(ports)

    def handle_serial_data(self, data):
        if self.echo_cb.isChecked():
            self.serial_terminal.append(f"RECV: {data}")


    def connect_port(self):
        if self.connect_btn.text() == "Connect":
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            if self.tester.connect(port, baud):
                self.connect_btn.setText("Disconnect")
                self.debug_terminal.append(f"Connected to {port} at {baud} baud")
                # Start serial monitor
                self.serial_monitor.start_monitoring(self.tester.serial_port,
                                                     self.handle_serial_data)
            else:
                self.debug_terminal.append("Connection failed")
        else:
            self.serial_monitor.stop_monitoring()
            self.tester.disconnect()
            self.connect_btn.setText("Connect")
            self.debug_terminal.append("Disconnected")

    def generate_data(self):
        duration = self.duration_spin.value()
        noise = self.noise_spin.value()
        self.timestamps, self.test_data = self.tester.generate_test_data(duration, noise)
        self.debug_terminal.append(f"Generated test data: {duration}s, noise level {noise}")

    def visualize_data(self):
        self.tester.visualize_test_data()

    def send_data(self):
        if not hasattr(self, 'test_data') or not self.test_data:
            self.debug_terminal.append("No test data available. Generate data first.")
            return

        if not self.tester.serial_port:
            self.debug_terminal.append("Not connected to serial port")
            return

        self.test_running = True
        self.current_sample = 0
        self.stop_btn.setEnabled(True)
        self.send_btn.setEnabled(False)
        interval = self.interval_spin.value()
        self.send_timer.start(interval)
        self.debug_terminal.append(f"Started sending data with {interval}ms interval")

    def stop_test(self):
        self.test_running = False
        self.send_timer.stop()
        self.stop_btn.setEnabled(False)
        self.send_btn.setEnabled(True)
        self.debug_terminal.append("Test stopped")

    def send_next_data(self):
        if not self.test_running or self.current_sample >= len(self.test_data[0]):
            self.stop_test()
            return

        try:
            # Format data packet
            timestamp = int(time.time() * 1000)
            packet = f"START,{timestamp},"

            # Add sensor readings
            for s in range(16):
                for board in range(2):
                    packet += f"S{s + 1}A{board}:{self.test_data[s][self.current_sample]},"

            packet += "END\n"

            # Send data
            self.tester.serial_port.write(packet.encode())

            # Update debug information
            if self.raw_data_cb.isChecked():
                self.raw_terminal.append(f"SENT: {packet.strip()}")

            if self.parsed_data_cb.isChecked():
                parsed_data = f"Sample {self.current_sample}: "
                for s in range(16):
                    parsed_data += f"S{s + 1}={self.test_data[s][self.current_sample]} "
                self.debug_terminal.append(parsed_data)

            if self.timing_cb.isChecked():
                self.debug_terminal.append(f"Time: {timestamp}ms")

            self.current_sample += 1

        except Exception as e:
            self.debug_terminal.append(f"Error sending data: {str(e)}")
            self.stop_test()


class SensorArrayTester:
    def __init__(self, gui=None):
        self.num_sensors = 16
        self.serial_port = None
        self.test_data = []
        self.gui = gui

    def connect(self, port, baud=115200):
        try:
            self.serial_port = serial.Serial(port, baud, timeout=1)
            time.sleep(2)  # Wait for Arduino reset
            return True
        except Exception as e:
            if self.gui:
                self.gui.debug_terminal.append(f"Connection error: {str(e)}")
            return False

    def disconnect(self):
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None

    def generate_test_data(self, duration=10, noise_level=0.1):
        """Generate binary sensor data with correlated falling edges"""
        sample_rate = 5  # Hz
        num_samples = int(duration * sample_rate)
        timestamps = np.linspace(0, duration, num_samples)

        # Create base signal first for correlation
        base_signal = np.zeros(num_samples)

        # Add pulses to base signal
        num_pulses = random.randint(2, 4)  # 2-4 pulses total
        for _ in range(num_pulses):
            start_idx = random.randint(0, num_samples - int(sample_rate))
            fall_duration = int(sample_rate * 0.5)  # 0.5 seconds fall time

            # Create the pulse with falling edge
            base_signal[start_idx] = 1023

            # Create exponential decay
            fall_indices = np.arange(fall_duration)
            decay = 1023 * np.exp(-3 * fall_indices / fall_duration)

            # Apply decay pattern
            for j, val in enumerate(decay):
                if start_idx + j < num_samples:
                    base_signal[start_idx + j] = val

        # Generate correlated signals for all sensors
        self.test_data = []
        variation_range = 0.15  # 15% maximum variation

        # Define sensor positions in 4x4 grid
        grid_positions = [(x, y) for x in range(4) for y in range(4)]
        center_x, center_y = 1.5, 1.5  # Center of the 4x4 grid

        for i, (grid_x, grid_y) in enumerate(grid_positions):
            # Calculate distance from center to create variation
            distance = np.sqrt((grid_x - center_x) ** 2 + (grid_y - center_y) ** 2)
            max_distance = np.sqrt(2 * 2 + 2 * 2)  # Maximum possible distance
            distance_factor = 1 - (distance / max_distance * variation_range)

            # Create correlated signal with position-based variation
            signal = base_signal * distance_factor

            # Add small random variation (keeping within variation range)
            random_variation = 1 + np.random.uniform(-variation_range / 2, variation_range / 2, num_samples)
            signal = signal * random_variation

            # Add minimal noise
            noise = np.random.normal(0, noise_level * 20, num_samples)  # Reduced noise
            signal = signal + noise

            # Clip values to valid range
            signal = np.clip(signal, 0, 1023)
            signal = signal.astype(int)

            self.test_data.append(signal)

        # Add slight time delays based on position
        max_delay_samples = int(sample_rate * 0.1)  # Maximum 0.1 second delay
        for i, (grid_x, grid_y) in enumerate(grid_positions):
            if i > 0:  # Skip first sensor
                distance = np.sqrt((grid_x - center_x) ** 2 + (grid_y - center_y) ** 2)
                delay_samples = int(distance / max_distance * max_delay_samples)
                if delay_samples > 0:
                    # Shift signal and pad with zeros
                    self.test_data[i] = np.pad(self.test_data[i][:-delay_samples],
                                               (delay_samples, 0),
                                               'constant')

        return timestamps, self.test_data
    def visualize_test_data(self):
        """Plot test data for verification"""
        if not self.test_data:
            if self.gui:
                self.gui.debug_terminal.append("No test data to visualize")
            return

        fig, axes = plt.subplots(4, 4, figsize=(15, 15))
        timestamps = np.linspace(0, 10, len(self.test_data[0]))

        for i in range(4):
            for j in range(4):
                sensor_idx = i * 4 + j
                axes[i, j].plot(timestamps, self.test_data[sensor_idx])
                axes[i, j].set_title(f'Sensor {sensor_idx + 1}')
                axes[i, j].grid(True)

        plt.tight_layout()
        plt.show()


def main():
    app = QApplication([])
    window = SensorDebugGUI()
    window.show()
    app.exec_()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Application error: {str(e)}")
        sys.exit(1)
