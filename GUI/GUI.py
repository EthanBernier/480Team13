import sys
import serial
import time
from serial.tools import list_ports
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QPushButton, QLabel,
                             QComboBox, QTextEdit, QFrame, QMessageBox,
                             QDialog, QLineEdit, QGroupBox, QSpinBox, QProgressBar, QTabWidget)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette
import pyqtgraph as pg
import random
from scipy.signal import find_peaks
import os
import csv
from datetime import datetime
import numpy as np

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QPushButton, QLabel,
                             QComboBox, QTextEdit, QFrame, QMessageBox,
                             QDialog, QLineEdit, QGroupBox, QSpinBox,
                             QCheckBox, QProgressBar, QFileDialog)  # Added missing widgets

TEST_MODE = False
# Use simulator if TEST_MODE environment variable is set or if no real ports are available
try:
    # Try to get real ports first
    real_ports = list_ports.comports()
    if not real_ports or TEST_MODE:
        # If no real ports or TEST_MODE is set, use simulator
        from sensor_simulator import MockSerial, MockListPorts

        serial.Serial = MockSerial
        serial.tools.list_ports = MockListPorts
        print("Using sensor simulator")
    else:
        print(f"Found {len(real_ports)} real serial ports")
except Exception as e:
    print(f"Error checking ports: {str(e)}")
    # Fall back to simulator
    from sensor_simulator import MockSerial, MockListPorts

    serial.Serial = MockSerial
    serial.tools.list_ports = MockListPorts
    print("Falling back to sensor simulator")

FAN_COLORS = {
    'Off': '#FFFFFF',  # White
    'Low': '#90EE90',  # Light Green
    'Medium': '#4CAF50',  # Medium Green
    'High': '#1B5E20'  # Dark Green
}


class SprayPatternDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Spray Pattern")
        layout = QVBoxLayout()

        # Pattern input
        pattern_group = QGroupBox("Spray Pattern")
        pattern_layout = QVBoxLayout()

        # Binary input
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Enter binary pattern (e.g., 1010)")
        pattern_layout.addWidget(QLabel("Pattern (1 = spray, 0 = wait):"))
        pattern_layout.addWidget(self.pattern_input)

        # Add pattern validation
        self.pattern_input.textChanged.connect(self.validate_pattern)
        pattern_group.setLayout(pattern_layout)
        layout.addWidget(pattern_group)

        # Cycle duration
        timing_group = QGroupBox("Timing")
        timing_layout = QHBoxLayout()
        self.cycle_duration = QSpinBox()
        self.cycle_duration.setRange(100, 10000)  # 100ms to 10 seconds
        self.cycle_duration.setValue(1000)  # Default 1 second
        self.cycle_duration.setSuffix(" ms")
        timing_layout.addWidget(QLabel("Cycle Duration:"))
        timing_layout.addWidget(self.cycle_duration)
        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)

        # Total time calculation
        self.total_time_label = QLabel("Total Time: 0 seconds")
        layout.addWidget(self.total_time_label)

        # Pattern visualization
        self.visualization = QTextEdit()
        self.visualization.setReadOnly(True)
        self.visualization.setMaximumHeight(100)
        layout.addWidget(QLabel("Pattern Visualization:"))
        layout.addWidget(self.visualization)

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

    def validate_pattern(self):
        """Validate the pattern and update visualization"""
        pattern = self.pattern_input.text()
        if not all(c in '01' for c in pattern):
            self.pattern_input.setStyleSheet("background-color: #FFE4E1;")
            return False

        self.pattern_input.setStyleSheet("")
        self.update_visualization()
        return True

    def update_visualization(self):
        """Update the pattern visualization and total time"""
        pattern = self.pattern_input.text()
        cycle_time = self.cycle_duration.value() / 1000.0  # Convert to seconds
        total_time = len(pattern) * cycle_time

        # Update total time label
        self.total_time_label.setText(f"Total Time: {total_time:.1f} seconds")

        # Create visualization
        viz_text = "Timeline:\n"
        for i, bit in enumerate(pattern):
            if bit == '1':
                viz_text += f"{i * cycle_time:.1f}s: Spray for {cycle_time:.1f}s\n"
            else:
                viz_text += f"{i * cycle_time:.1f}s: Wait for {cycle_time:.1f}s\n"

        self.visualization.setText(viz_text)

    def get_settings(self):
        """Return the current pattern and timing settings"""
        return {
            'pattern': self.pattern_input.text(),
            'cycle_duration': self.cycle_duration.value()
        }


class PortSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Store reference to parent
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
        self.fan_baud.setCurrentText('115200')
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

    def refresh_ports(self):
        """Refresh the list of available ports"""
        try:
            ports = [port.device for port in list_ports.comports()]
            self.fan_port_combo.clear()
            self.sensor_port_combo.clear()

            if ports:
                self.fan_port_combo.addItems(ports)
                self.sensor_port_combo.addItems(ports)
            else:
                self.fan_port_combo.addItem("No ports found")
                self.sensor_port_combo.addItem("No ports found")

            if self.parent:
                self.parent.log_terminal.append("Port list refreshed")

        except Exception as e:
            if self.parent:
                self.parent.log_terminal.append(f"Error refreshing ports: {str(e)}")
            QMessageBox.warning(self, "Port Refresh Error", f"Error refreshing ports: {str(e)}")

    def get_selected_ports(self):
        try:
            # Get fan port (prefer manual entry if provided)
            fan_port = (self.fan_port_manual.text() if self.fan_port_manual.text()
                        else self.fan_port_combo.currentText())

            # Get sensor port (prefer manual entry if provided)
            sensor_port = (self.sensor_port_manual.text() if self.sensor_port_manual.text()
                           else self.sensor_port_combo.currentText())

            # Get baud rates
            fan_baud = int(self.fan_baud.currentText())
            sensor_baud = int(self.sensor_baud.currentText())

            return fan_port, sensor_port, fan_baud, sensor_baud
        except Exception as e:
            QMessageBox.warning(self, "Port Selection Error", f"Error getting port selection: {str(e)}")
            return None, None, 9600, 115200


class SensorArrayGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fan Array Control Interface v.1.00x`")
        self.setGeometry(100, 100, 1600, 1000)

        # Initialize variables first
        self.fan_serial = None
        self.sensor_serial = None
        self.pattern_delay = 0.1
        self.start_time = time.time()

        # Initialize detection settings before creating plots
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 1023)
        self.threshold_spin.setValue(500)

        self.peak_height_spin = QSpinBox()
        self.peak_height_spin.setRange(0, 1023)
        self.peak_height_spin.setValue(700)

        self.peak_distance_spin = QSpinBox()
        self.peak_distance_spin.setRange(1, 100)
        self.peak_distance_spin.setValue(20)

        # In __init__
        self.sensor_buffers = {i: [] for i in range(32)}  # Changed from 10 to 32
        self.SMOOTHING_WINDOW = 3
        self.SMOOTHED_SENSORS = set(range(0, 32))  # Second multiplexer sensors are smoothed
        self.bit_detectors = {}
        self.setup_bit_detectors()
        self.setup_ui()

    def show_experiment_automation(self):
        dialog = ExperimentAutomationDialog(self)
        dialog.exec_()

    def setup_ui(self):
        # Set plot configs
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Experimental Automation
        experiment_btn = QPushButton("Experiment Automation")
        experiment_btn.clicked.connect(self.show_experiment_automation)
        left_layout.addWidget(experiment_btn)

        #record data
        recording_panel = self.create_recording_panel()
        left_layout.addWidget(recording_panel)

        # Add fan control panel (only once)
        fan_panel = self.create_fan_panel()
        left_layout.addWidget(fan_panel)

        # Add sprayer panel
        sprayer_panel = self.create_sprayer_panel()
        left_layout.addWidget(sprayer_panel)

        # Create log terminal and layout
        self.log_terminal = QTextEdit()
        self.log_terminal.setReadOnly(True)
        self.log_terminal.setMaximumHeight(200)

        log_layout = QVBoxLayout()
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("Debug Log:"))
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.log_terminal.clear)
        log_header.addWidget(clear_log_btn)
        log_layout.addLayout(log_header)
        log_layout.addWidget(self.log_terminal)
        left_layout.addLayout(log_layout)

        # Add detection panel
        detection_panel = self.create_detection_panel()
        left_layout.addWidget(detection_panel)


        # Create sensor plots list before creating tabs
        self.sensor_plots = []

        # Create tab widget for multiplexer plots
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_mux_panel(0), "Multiplexer 1 (S1-S16)")
        self.tab_widget.addTab(self.create_mux_panel(1), "Multiplexer 2 (S17-S32)")

        # Add panels to main layout
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(self.tab_widget, stretch=2)

        # Setup timers
        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.update_sensor_data)
        self.sensor_timer.start(200)

        self.pattern_timer = QTimer()
        self.pattern_timer.timeout.connect(self.update_fan_pattern)
        self.pattern_timer.start(5000)

        # Log startup
        self.log_terminal.append("Application initialized")

    def smooth_value(self, values):
        """Calculate moving average of the last n values"""
        return sum(values) / len(values) if values else 0

    def create_recording_panel(self):
        """Create a panel for quick data recording"""
        recording_panel = QFrame()
        recording_panel.setFrameStyle(QFrame.Panel | QFrame.Raised)
        layout = QHBoxLayout(recording_panel)

        # Duration input with label
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration (s):"))
        self.record_duration = QSpinBox()
        self.record_duration.setRange(1, 3600)  # 1 second to 1 hour
        self.record_duration.setValue(60)  # Default 60 seconds
        duration_layout.addWidget(self.record_duration)
        layout.addLayout(duration_layout)

        # Record button
        self.record_btn = QPushButton("Record Data")
        self.record_btn.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_btn)

        return recording_panel

    def toggle_recording(self):
        """Start or stop data recording"""
        if not hasattr(self, 'recording_active') or not self.recording_active:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start recording sensor data"""
        try:
            # Create data directory if it doesn't exist
            if not os.path.exists('recorded_data'):
                os.makedirs('recorded_data')

            # Create new data file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.data_file = open(f"recorded_data/sensor_data_{timestamp}.csv", "w", newline='')
            self.csv_writer = csv.writer(self.data_file)

            # Write header
            self.csv_writer.writerow(['Timestamp', 'Elapsed_Time', 'Sensor_ID', 'Value'])

            # Initialize recording variables
            self.recording_active = True
            self.record_start_time = time.time()
            self.record_end_time = self.record_start_time + self.record_duration.value()

            # Update UI
            self.record_btn.setText("Stop Recording")
            self.record_duration.setEnabled(False)
            self.log_terminal.append(f"Started recording for {self.record_duration.value()} seconds")

            # Start recording timer
            self.recording_timer = QTimer()
            self.recording_timer.timeout.connect(self.record_data)
            self.recording_timer.start(100)  # Record every 100ms

        except Exception as e:
            self.log_terminal.append(f"Error starting recording: {str(e)}")
            self.stop_recording()

    def record_data(self):
        """Record current sensor data"""
        try:
            current_time = time.time()
            elapsed_time = current_time - self.record_start_time

            # Check if recording should end
            if current_time >= self.record_end_time:
                self.stop_recording()
                return

            # Record data from all sensors
            for sensor_id in range(32):  # For all 32 sensors
                if sensor_id < len(self.sensor_plots):
                    plot = self.sensor_plots[sensor_id]
                    if plot['data']['y']:
                        value = plot['data']['y'][-1]  # Get most recent value
                        self.csv_writer.writerow([
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                            f"{elapsed_time:.3f}",
                            sensor_id + 1,  # 1-based sensor ID
                            value
                        ])

        except Exception as e:
            self.log_terminal.append(f"Error recording data: {str(e)}")
            self.stop_recording()

    def stop_recording(self):
        """Stop recording sensor data"""
        try:
            if hasattr(self, 'recording_active') and self.recording_active:
                self.recording_active = False
                if hasattr(self, 'recording_timer'):
                    self.recording_timer.stop()
                if hasattr(self, 'data_file'):
                    self.data_file.close()

                # Update UI
                self.record_btn.setText("Record Data")
                self.record_duration.setEnabled(True)
                self.log_terminal.append("Recording stopped")

        except Exception as e:
            self.log_terminal.append(f"Error stopping recording: {str(e)}")
    def create_mux_panel(self, mux_index):
        """Create a panel for 16 sensors from one multiplexer"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Add MUX info header
        header = QHBoxLayout()
        header.addWidget(QLabel(f"Multiplexer {mux_index + 1} Sensors"))
        if mux_index == 1:
            header.addWidget(QLabel("(Smoothed)"))
        layout.addLayout(header)

        # Create grid for plots
        plot_grid = QGridLayout()
        base_sensor = mux_index * 16  # 0 for MUX1, 16 for MUX2

        # Create 4x4 grid of plots
        for i in range(16):
            row = i // 4
            col = i % 4
            sensor_num = base_sensor + i

            plot_widget = pg.PlotWidget()
            plot_widget.setBackground('w')
            plot_widget.setTitle(f'S{sensor_num + 1} (CH{i})')
            plot_widget.setLabel('left', 'Value')
            plot_widget.setLabel('bottom', 'Time (s)')
            plot_widget.showGrid(x=True, y=True)

            # Configure axes
            for ax in ['left', 'bottom']:
                plot_widget.getAxis(ax).setPen('k')
                plot_widget.getAxis(ax).setTextPen('k')

            # Set ranges
            plot_widget.setYRange(0, 1023, padding=0.1)
            plot_widget.setXRange(-30, 0, padding=0.1)

            # Create plot elements
            curve = plot_widget.plot(pen=pg.mkPen('b', width=2 if mux_index == 1 else 1))
            threshold_line = plot_widget.addLine(y=self.threshold_spin.value(),
                                                 pen=pg.mkPen('r', style=Qt.DashLine))
            peaks_scatter = pg.ScatterPlotItem(pen=None, symbol='o', size=8, brush=pg.mkBrush('g'))
            crossings_scatter = pg.ScatterPlotItem(pen=None, symbol='x', size=8, brush=pg.mkBrush('r'))

            plot_widget.addItem(peaks_scatter)
            plot_widget.addItem(crossings_scatter)

            plot_grid.addWidget(plot_widget, row, col)

            self.sensor_plots.append({
                'widget': plot_widget,
                'curve': curve,
                'threshold_line': threshold_line,
                'peaks_scatter': peaks_scatter,
                'crossings_scatter': crossings_scatter,
                'data': {'x': [], 'y': []}
            })

        layout.addLayout(plot_grid)

        # Add control row at bottom
        control_row = QHBoxLayout()

        # Add auto-scale button
        auto_scale_btn = QPushButton("Auto Scale")
        auto_scale_btn.clicked.connect(lambda: self.auto_scale_mux(mux_index))
        control_row.addWidget(auto_scale_btn)

        # Add reset view button
        reset_view_btn = QPushButton("Reset View")
        reset_view_btn.clicked.connect(lambda: self.reset_mux_view(mux_index))
        control_row.addWidget(reset_view_btn)

        layout.addLayout(control_row)
        return panel

    def auto_scale_mux(self, mux_index):
        """Auto-scale all plots for a multiplexer"""
        start_idx = mux_index * 16
        for i in range(16):
            plot = self.sensor_plots[start_idx + i]
            plot['widget'].enableAutoRange()

    def reset_mux_view(self, mux_index):
        """Reset view for all plots in a multiplexer"""
        start_idx = mux_index * 16
        for i in range(16):
            plot = self.sensor_plots[start_idx + i]
            plot['widget'].setYRange(0, 1023, padding=0.1)
            if len(plot['data']['x']) > 0:
                latest_time = plot['data']['x'][-1]
                plot['widget'].setXRange(latest_time - 30, latest_time)

    def update_sensor_data(self):
        """Update sensor data with improved error handling"""
        if not self.sensor_serial:
            if not hasattr(self, '_no_serial_logged'):
                self.log_terminal.append("No sensor serial connection available")
                self._no_serial_logged = True
            return

        try:
            if self.sensor_serial.in_waiting:
                line = self.sensor_serial.readline().decode().strip()
                self.log_terminal.append(f"Raw data: {line}")  # Debug line

                try:
                    if line.startswith("START") and line.endswith("END"):
                        parts = line.split(',')

                        # Validate data format
                        if len(parts) < 4:  # START + timestamp + at least one sensor + END
                            self.log_terminal.append(f"Invalid data format - not enough parts: {line}")
                            return

                        timestamp = time.time() - self.start_time

                        # Process sensor readings
                        for part in parts[2:-1]:  # Skip START, timestamp, and END
                            if ':' in part and part.startswith('S'):
                                try:
                                    sensor_str, value_str = part.split(':')
                                    sensor_num = int(sensor_str.replace('S', '')) - 1  # Convert to 0-based index
                                    raw_value = float(value_str)

                                    # Add value to buffer for smoothing
                                    if sensor_num in self.sensor_buffers:
                                        self.sensor_buffers[sensor_num].append(raw_value)
                                        if len(self.sensor_buffers[sensor_num]) > self.SMOOTHING_WINDOW:
                                            self.sensor_buffers[sensor_num].pop(0)

                                    # Apply smoothing for appropriate sensors
                                    value = self.smooth_value(self.sensor_buffers[
                                                                  sensor_num]) if sensor_num in self.SMOOTHED_SENSORS else raw_value

                                    # Update plot if valid sensor number
                                    if 0 <= sensor_num < len(self.sensor_plots):
                                        self.update_plot(sensor_num, timestamp, value)

                                        # Log occasionally
                                        if timestamp % 5 < 0.1:
                                            if sensor_num in self.SMOOTHED_SENSORS:
                                                self.log_terminal.append(
                                                    f"Sensor {sensor_num + 1}: raw={raw_value:.2f}, smoothed={value:.2f}")
                                            else:
                                                self.log_terminal.append(f"Sensor {sensor_num + 1}: value={value:.2f}")

                                except ValueError as ve:
                                    self.log_terminal.append(f"Value error parsing sensor {sensor_str}: {ve}")
                                except Exception as e:
                                    self.log_terminal.append(f"Error processing sensor {sensor_str}: {e}")

                    elif not line.startswith("Fan"):  # Ignore fan control messages
                        self.log_terminal.append(f"Unknown data format: {line}")

                except Exception as e:
                    self.log_terminal.append(f"Error parsing line: {str(e)}\nLine content: {line}")

        except Exception as e:
            self.log_terminal.append(f"Serial read error: {str(e)}")

    def process_plot_data(self, plot_index):
        """Process plot data with peak detection"""
        try:
            from scipy.signal import find_peaks

            plot = self.sensor_plots[plot_index]
            if len(plot['data']['y']) > 1:
                y_data = np.array(plot['data']['y'])
                x_data = np.array(plot['data']['x'])
                threshold = self.threshold_spin.value()

                # Find peaks if enough data points
                if len(y_data) > self.peak_distance_spin.value():
                    peaks, _ = find_peaks(y_data,
                                          height=self.peak_height_spin.value(),
                                          distance=self.peak_distance_spin.value())

                    # Update peaks scatter plot
                    if len(peaks) > 0:
                        plot['peaks_scatter'].setData(
                            x=x_data[peaks],
                            y=y_data[peaks]
                        )
                    else:
                        plot['peaks_scatter'].clear()

                    # Find threshold crossings (falling edges)
                    crossings = []
                    for i in range(1, len(y_data)):
                        if y_data[i - 1] >= threshold and y_data[i] < threshold:
                            crossings.append(i)

                    # Update crossings scatter plot
                    if len(crossings) > 0:
                        plot['crossings_scatter'].setData(
                            x=x_data[crossings],
                            y=[threshold] * len(crossings)
                        )
                    else:
                        plot['crossings_scatter'].clear()

        except Exception as e:
            # Only log peak detection errors once
            if not hasattr(self, '_peak_error_logged'):
                self.log_terminal.append(f"Peak detection disabled: {str(e)}")
                self._peak_error_logged = True

    def create_fan_panel(self):
        """Create fan control panel"""
        fan_panel = QFrame()
        fan_panel.setFrameStyle(QFrame.Panel | QFrame.Raised)
        fan_layout = QVBoxLayout(fan_panel)

        # Connection status and port selection
        connection_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect Devices")
        self.connect_btn.clicked.connect(self.show_port_selection)
        connection_layout.addWidget(self.connect_btn)

        # Fan array (4x4 grid of buttons)
        fan_grid = self.setup_fan_grid()

        # Fan controls
        self.fan_mode = QComboBox()
        self.fan_mode.addItems(["Random Power", "Custom", "All On", "All Off"])
        self.fan_mode.currentTextChanged.connect(self.change_fan_mode)

        speed_layout = QHBoxLayout()
        self.speed_select = QComboBox()
        self.speed_select.addItems(["Off", "Low", "Medium", "High"])
        speed_layout.addWidget(QLabel("Fan Speed:"))
        speed_layout.addWidget(self.speed_select)

        # Add all controls to panel
        fan_layout.addLayout(connection_layout)
        fan_layout.addWidget(QLabel("Fan Control Array"))
        fan_layout.addLayout(fan_grid)
        fan_layout.addWidget(QLabel("Programs:"))
        fan_layout.addWidget(self.fan_mode)
        fan_layout.addLayout(speed_layout)

        return fan_panel

    def create_sprayer_panel(self):
        """Create sprayer control panel"""
        sprayer_panel = QFrame()
        sprayer_panel.setFrameStyle(QFrame.Panel | QFrame.Raised)
        sprayer_layout = QVBoxLayout(sprayer_panel)
        sprayer_layout.addWidget(QLabel("Sprayer Control"))

        # Pattern input and display
        pattern_layout = QHBoxLayout()
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Enter binary pattern (e.g., 1010)")
        pattern_layout.addWidget(QLabel("Pattern:"))
        pattern_layout.addWidget(self.pattern_input)
        sprayer_layout.addLayout(pattern_layout)

        # Timing controls
        timing_layout = QGridLayout()
        self.cycle_duration = QSpinBox()
        self.cycle_duration.setRange(100, 60000)
        self.cycle_duration.setValue(1000)
        self.cycle_duration.setSuffix(" ms")
        timing_layout.addWidget(QLabel("Cycle Duration:"), 0, 0)
        timing_layout.addWidget(self.cycle_duration, 0, 1)

        # Pattern controls
        control_layout = QHBoxLayout()
        self.start_pattern_btn = QPushButton("Start Pattern")
        self.stop_pattern_btn = QPushButton("Stop Pattern")
        self.start_pattern_btn.clicked.connect(self.start_spray_pattern)
        self.stop_pattern_btn.clicked.connect(self.stop_spray_pattern)
        self.stop_pattern_btn.setEnabled(False)
        control_layout.addWidget(self.start_pattern_btn)
        control_layout.addWidget(self.stop_pattern_btn)

        sprayer_layout.addLayout(timing_layout)
        sprayer_layout.addLayout(control_layout)

        # Status display
        self.spray_status = QLabel("Status: Idle")
        sprayer_layout.addWidget(self.spray_status)

        return sprayer_panel

    def create_detection_panel(self):
        """Create detection settings panel"""
        detection_panel = QFrame()
        detection_panel.setFrameStyle(QFrame.Panel | QFrame.Raised)
        detection_layout = QVBoxLayout(detection_panel)
        detection_layout.addWidget(QLabel("Detection Settings"))

        # Detection controls
        controls_layout = QGridLayout()

        # Threshold control
        controls_layout.addWidget(QLabel("Threshold:"), 0, 0)
        controls_layout.addWidget(self.threshold_spin, 0, 1)

        # Peak height control
        controls_layout.addWidget(QLabel("Peak Height:"), 1, 0)
        controls_layout.addWidget(self.peak_height_spin, 1, 1)

        # Peak distance control
        controls_layout.addWidget(QLabel("Peak Distance:"), 2, 0)
        controls_layout.addWidget(self.peak_distance_spin, 2, 1)

        detection_layout.addLayout(controls_layout)

        # Auto threshold button
        auto_threshold_btn = QPushButton("Auto Threshold")
        auto_threshold_btn.clicked.connect(self.calculate_auto_threshold)
        detection_layout.addWidget(auto_threshold_btn)

        return detection_panel

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
                if fan_port or sensor_port:  # Connect if at least one port is selected
                    self.connect_devices(fan_port, sensor_port, fan_baud, sensor_baud)
        except Exception as e:
            self.log_terminal.append(f"Port selection error: {str(e)}")
            QMessageBox.warning(self, "Error", f"Port selection failed: {str(e)}")

    def connect_devices(self, fan_port, sensor_port, fan_baud=9600, sensor_baud=11520):
        """Improved device connection handling"""
        # Close existing connections first
        if self.fan_serial:
            try:
                self.fan_serial.close()
            except:
                pass
            self.fan_serial = None

        if self.sensor_serial:
            try:
                self.sensor_serial.close()
            except:
                pass
            self.sensor_serial = None

        # Connect to fan controller
        if fan_port and fan_port != "No ports found":
            try:
                self.fan_serial = serial.Serial(
                    port=fan_port,
                    baudrate=fan_baud,
                    timeout=0.1,  # 100ms timeout
                    write_timeout=1
                )
                time.sleep(2)  # Wait for Arduino reset
                self.log_terminal.append(f"Connected to fan controller on {fan_port}")
            except Exception as e:
                self.log_terminal.append(f"Fan controller connection error: {str(e)}")
                self.fan_serial = None
                QMessageBox.warning(self, "Connection Error",
                                    f"Failed to connect to fan controller: {str(e)}")

        # Connect to sensor controller
        if sensor_port and sensor_port != "No ports found":
            try:
                self.sensor_serial = serial.Serial(
                    port=sensor_port,
                    baudrate=sensor_baud,
                    timeout=0.1,  # 100ms timeout
                    write_timeout=1
                )
                time.sleep(2)  # Wait for Arduino reset
                self.log_terminal.append(f"Connected to sensor controller on {sensor_port}")
            except Exception as e:
                self.log_terminal.append(f"Sensor controller connection error: {str(e)}")
                self.sensor_serial = None
                QMessageBox.warning(self, "Connection Error",
                                    f"Failed to connect to sensor controller: {str(e)}")

    def create_fan_button(self, i, j, fan_num):
        """Create a fan button with proper event handling"""
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setMinimumSize(50, 50)
        # Store the fan number as a property of the button
        btn.fan_number = fan_num
        btn.clicked.connect(lambda checked, b=btn: self.toggle_fan(b.fan_number))
        return btn

    def setup_fan_grid(self):
        """Setup the fan control grid with proper button initialization"""
        fan_grid = QGridLayout()
        self.fan_buttons = []
        for i in range(4):
            row = []
            for j in range(4):
                fan_num = i * 4 + j
                btn = self.create_fan_button(i, j, fan_num)
                fan_grid.addWidget(btn, i, j)
                row.append(btn)
            self.fan_buttons.append(row)
        return fan_grid

    def change_fan_mode(self, mode):
        """Handle fan mode changes without blocking"""
        if mode == "All On":
            for i in range(4):
                for j in range(4):
                    button = self.fan_buttons[i][j]
                    button.setChecked(True)
                    button.setStyleSheet("background-color: green;")
                    self.queue_fan_command(i * 4 + j, self.speed_select.currentIndex())

        elif mode == "All Off":
            for i in range(4):
                for j in range(4):
                    button = self.fan_buttons[i][j]
                    button.setChecked(False)
                    button.setStyleSheet("")
                    self.queue_fan_command(i * 4 + j, 0)

        elif mode == "Random Power":
            for i in range(4):
                for j in range(4):
                    button = self.fan_buttons[i][j]
                    is_on = random.choice([True, False])
                    button.setChecked(is_on)
                    button.setStyleSheet("background-color: green;" if is_on else "")
                    if is_on:
                        self.queue_fan_command(i * 4 + j, self.speed_select.currentIndex())
                    else:
                        self.queue_fan_command(i * 4 + j, 0)

        # Process the command queue
        self.process_fan_commands()

    def queue_fan_command(self, fan_num, speed):
        """Queue a fan command instead of sending immediately"""
        if not hasattr(self, 'fan_command_queue'):
            self.fan_command_queue = []
        self.fan_command_queue.append((fan_num, speed))

    def process_fan_commands(self):
        """Process queued fan commands with a timer to prevent blocking"""
        if not hasattr(self, 'fan_command_queue'):
            return

        if not hasattr(self, 'command_timer'):
            self.command_timer = QTimer()
            self.command_timer.timeout.connect(self.send_next_command)
            self.command_timer.setInterval(50)  # 50ms between commands

        if self.fan_command_queue and not self.command_timer.isActive():
            self.command_timer.start()

    def send_next_command(self):
        """Send the next fan command in the queue"""
        if hasattr(self, 'fan_command_queue') and self.fan_command_queue:
            if self.fan_serial:
                try:
                    fan_num, speed = self.fan_command_queue.pop(0)
                    command = f"{fan_num},{speed}\n"
                    self.fan_serial.write(command.encode())
                except Exception as e:
                    self.log_terminal.append(f"Fan control error: {str(e)}")
        else:
            self.command_timer.stop()

    def toggle_fan(self, fan_num):
        """Improved fan toggle function"""
        if self.fan_serial:
            try:
                row = fan_num // 4
                col = fan_num % 4
                button = self.fan_buttons[row][col]

                if button.isChecked():
                    speed = self.speed_select.currentIndex()
                    command = f"{fan_num},{speed}\n"
                    button.setStyleSheet(f"background-color: {FAN_COLORS[self.speed_select.currentText()]}")
                else:
                    command = f"{fan_num},0\n"
                    button.setStyleSheet("")

                self.fan_serial.write(command.encode())
                self.log_terminal.append(f"Fan {fan_num} {'activated' if button.isChecked() else 'deactivated'}")

            except Exception as e:
                self.log_terminal.append(f"Fan control error: {str(e)}")
                QMessageBox.warning(self, "Fan Control Error", str(e))

    def setup_bit_detectors(self):
        """Initialize bit detectors for each sensor"""
        for i in range(32):  # Changed from 10 to 32
            self.bit_detectors[i] = BitDetector(threshold=250)

    def update_plot(self, plot_index, timestamp, value):
        """Update plot with check for visible tab"""
        try:
            # Only update plots if their tab is visible
            mux_index = plot_index // 16
            if self.tab_widget.currentIndex() == mux_index:
                plot = self.sensor_plots[plot_index]

                # Store new data point
                plot['data']['x'].append(timestamp)
                plot['data']['y'].append(value)

                # Keep last 30 seconds of data
                current_time = timestamp
                while plot['data']['x'] and (current_time - plot['data']['x'][0]) > 30:
                    plot['data']['x'].pop(0)
                    plot['data']['y'].pop(0)

                # Update plot data with appropriate styling
                if plot_index in self.SMOOTHED_SENSORS:
                    plot['curve'].setData(
                        plot['data']['x'],
                        plot['data']['y'],
                        pen=pg.mkPen('b', width=2)
                    )
                else:
                    plot['curve'].setData(
                        plot['data']['x'],
                        plot['data']['y'],
                        pen=pg.mkPen('b', width=1)
                    )

                # Auto-scale Y axis if needed
                if len(plot['data']['y']) > 0:
                    ymin = min(plot['data']['y'])
                    ymax = max(plot['data']['y'])
                    padding = (ymax - ymin) * (0.15 if plot_index in self.SMOOTHED_SENSORS else 0.1)
                    if padding == 0:
                        padding = 0.1 * ymax if ymax != 0 else 1.0
                    plot['widget'].setYRange(ymin - padding, ymax + padding)

                # Update X axis to show moving 30-second window
                plot['widget'].setXRange(current_time - 30, current_time)

                # Update threshold line
                plot['threshold_line'].setValue(self.threshold_spin.value())

                # Perform bit detection
                detector = self.bit_detectors[plot_index]
                bit_detected, detection_time = detector.update(value, timestamp)

                if bit_detected:
                    self.log_terminal.append(
                        f"Bit detected on sensor {plot_index + 1} at t={detection_time:.2f}s"
                    )
                    # Add visual marker for detection
                    if not 'detections_scatter' in plot:
                        plot['detections_scatter'] = pg.ScatterPlotItem(
                            pen=None,
                            symbol='t',
                            size=15,
                            brush=pg.mkBrush('r')
                        )
                        plot['widget'].addItem(plot['detections_scatter'])

                    # Update detection markers
                    if len(detector.timestamps) > 0:
                        recent_detections = [
                            (t, v) for t, v in zip(detector.timestamps, detector.bits)
                            if timestamp - t <= 30
                        ]
                        if recent_detections:
                            times, values = zip(*recent_detections)
                            plot['detections_scatter'].setData(times, [self.threshold_spin.value()] * len(times))

        except Exception as e:
            if not hasattr(self, '_plot_errors'):
                self._plot_errors = set()
            error_key = f"{plot_index}:{str(e)}"
            if error_key not in self._plot_errors:
                self.log_terminal.append(f"Plot update error for sensor {plot_index + 1}: {str(e)}")
                self._plot_errors.add(error_key)

    def get_recent_bits(self, sensor_index, time_window=5.0):
        """Get bits detected in the last time_window seconds for a sensor"""
        detector = self.bit_detectors.get(sensor_index)
        if not detector:
            return []

        current_time = time.time() - self.start_time
        recent_bits = [
            bit for bit, t in zip(detector.bits, detector.timestamps)
            if current_time - t <= time_window
        ]
        return recent_bits

    def get_detection_stats(self, sensor_index):
        """Get detection statistics for a sensor"""
        detector = self.bit_detectors.get(sensor_index)
        if not detector:
            return {}

        return {
            'total_detections': detector.detection_count,
            'last_detection_time': detector.last_detection,
            'recent_bits': self.get_recent_bits(sensor_index)
        }

    def process_plot_data(self, plot_index):
        """Process current data for peaks and threshold crossings for a single plot"""
        try:
            plot = self.sensor_plots[plot_index]
            if len(plot['data']['y']) > 1:
                y_data = np.array(plot['data']['y'])
                x_data = np.array(plot['data']['x'])
                threshold = self.threshold_spin.value()

                # Find peaks if enough data points
                if len(y_data) > self.peak_distance_spin.value():
                    peaks, _ = find_peaks(y_data,
                                          height=self.peak_height_spin.value(),
                                          distance=self.peak_distance_spin.value())

                    # Update peaks scatter plot
                    if len(peaks) > 0:
                        plot['peaks_scatter'].setData(
                            x=x_data[peaks],
                            y=y_data[peaks]
                        )
                    else:
                        plot['peaks_scatter'].clear()

                    # Find threshold crossings (falling edges)
                    crossings = []
                    for i in range(1, len(y_data)):
                        if y_data[i - 1] >= threshold and y_data[i] < threshold:
                            crossings.append(i)

                    # Update crossings scatter plot
                    if len(crossings) > 0:
                        plot['crossings_scatter'].setData(
                            x=x_data[crossings],
                            y=[threshold] * len(crossings)
                        )
                    else:
                        plot['crossings_scatter'].clear()

        except Exception as e:
            self.log_terminal.append(f"Data processing error: {str(e)}")

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
                row = fan_num // 4
                col = fan_num % 4
                button = self.fan_buttons[row][col]

                if button.isChecked():
                    speed = self.speed_select.currentIndex()
                    command = f"{fan_num},{speed}\n"
                    button.setStyleSheet("background-color: green;")
                else:
                    command = f"{fan_num},0\n"
                    button.setStyleSheet("")

                self.fan_serial.write(command.encode())
                self.log_terminal.append(f"Fan {fan_num} {'activated' if button.isChecked() else 'deactivated'}")

            except Exception as e:
                self.log_terminal.append(f"Fan control error: {str(e)}")

    def change_fan_mode(self, mode):
        if mode == "All On":
            for i in range(4):
                for j in range(4):
                    button = self.fan_buttons[i][j]
                    button.setChecked(True)
                    button.setStyleSheet("background-color: green;")
                    if self.fan_serial:
                        try:
                            speed = self.speed_select.currentIndex()
                            self.fan_serial.write(f"{i * 4 + j},{speed}\n".encode())
                        except Exception as e:
                            self.log_terminal.append(f"Fan control error: {str(e)}")

        elif mode == "All Off":
            for i in range(4):
                for j in range(4):
                    button = self.fan_buttons[i][j]
                    button.setChecked(False)
                    button.setStyleSheet("")
                    if self.fan_serial:
                        try:
                            self.fan_serial.write(f"{i * 4 + j},0\n".encode())
                            time.sleep(self.pattern_delay)
                        except Exception as e:
                            self.log_terminal.append(f"Fan control error: {str(e)}")

        elif mode == "Random Power":
            for i in range(4):
                for j in range(4):
                    button = self.fan_buttons[i][j]
                    is_on = random.choice([True, False])
                    button.setChecked(is_on)
                    button.setStyleSheet("background-color: green;" if is_on else "")
                    if self.fan_serial and is_on:
                        try:
                            speed = self.speed_select.currentIndex()
                            self.fan_serial.write(f"{i * 4 + j},{speed}\n".encode())
                            time.sleep(self.pattern_delay)
                        except Exception as e:
                            self.log_terminal.append(f"Fan control error: {str(e)}")

        elif mode == "Waves":
            # Implement wave pattern here if needed
            pass

    def update_fan_pattern(self):
        if self.fan_mode.currentText() == "Random Power":
            self.change_fan_mode("Random Power")
        elif self.fan_mode.currentText() == "Waves":
            # Implement wave pattern here
            pass

    def start_spray_pattern(self):
        """Start the spray pattern sequence"""
        pattern = self.pattern_input.text()

        # Validate pattern
        if not pattern or not all(bit in '01' for bit in pattern):
            self.log_terminal.append("Invalid pattern. Please use only 0s and 1s.")
            return

        if not self.fan_serial:
            self.log_terminal.append("Fan controller not connected.")
            return

        try:
            # Send pattern configuration
            command = f"PATTERN,{pattern}\n"
            self.fan_serial.write(command.encode())

            # Send timing configuration
            cycle_time = self.cycle_duration.value()
            command = f"CYCLE,{cycle_time}\n"
            self.fan_serial.write(command.encode())

            # Update UI
            self.start_pattern_btn.setEnabled(False)
            self.stop_pattern_btn.setEnabled(True)
            self.pattern_input.setEnabled(False)
            self.cycle_duration.setEnabled(False)
            self.spray_status.setText("Status: Running Pattern")

            # Log start
            self.log_terminal.append(f"Started spray pattern: {pattern}")
            self.log_terminal.append(f"Cycle duration: {cycle_time}ms")

        except Exception as e:
            self.log_terminal.append(f"Error starting pattern: {str(e)}")

    def stop_spray_pattern(self):
        """Stop the spray pattern sequence"""
        if self.fan_serial:
            try:
                # Send stop command
                self.fan_serial.write(b"STOP\n")

                # Update UI
                self.start_pattern_btn.setEnabled(True)
                self.stop_pattern_btn.setEnabled(False)
                self.pattern_input.setEnabled(True)
                self.cycle_duration.setEnabled(True)
                self.spray_status.setText("Status: Idle")

                # Log stop
                self.log_terminal.append("Stopped spray pattern")

            except Exception as e:
                self.log_terminal.append(f"Error stopping pattern: {str(e)}")

    def update_detection_settings(self):
        """Update threshold lines and reprocess data"""
        threshold = self.threshold_spin.value()
        # Update all threshold lines
        for plot in self.sensor_plots:
            plot['threshold_line'].setValue(threshold)
        # Reprocess current data
        self.process_current_data()

    def calculate_auto_threshold(self):
        """Calculate threshold automatically based on current data"""
        all_values = []
        for plot in self.sensor_plots:
            if plot['data']['y']:
                all_values.extend(plot['data']['y'])

        if all_values:
            mean = np.mean(all_values)
            std = np.std(all_values)
            threshold = int(mean + 2 * std)  # 2 sigma threshold
            self.threshold_spin.setValue(threshold)
            self.log_terminal.append(f"Auto threshold set to: {threshold}")
        else:
            self.log_terminal.append("No data available for auto threshold")

    def process_current_data(self):
        """Process current data for peaks and threshold crossings"""

        for plot in self.sensor_plots:
            if len(plot['data']['y']) > 0:
                y_data = np.array(plot['data']['y'])
                x_data = np.array(plot['data']['x'])

                # Find peaks
                peaks, _ = find_peaks(y_data,
                                      height=self.peak_height_spin.value(),
                                      distance=self.peak_distance_spin.value())

                # Find threshold crossings (falling edges)
                threshold = self.threshold_spin.value()
                crossings = []
                for i in range(1, len(y_data)):
                    if y_data[i - 1] >= threshold and y_data[i] < threshold:
                        crossings.append(i)

                # Update scatter plots
                if len(peaks) > 0:
                    plot['peaks_scatter'].setData(x=x_data[peaks],
                                                  y=y_data[peaks])
                else:
                    plot['peaks_scatter'].clear()

                if len(crossings) > 0:
                    plot['crossings_scatter'].setData(
                        x=x_data[crossings],
                        y=[threshold] * len(crossings))
                else:
                    plot['crossings_scatter'].clear()

    def closeEvent(self, event):
        self.stop_spray_pattern()  # Stop any running pattern
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


class BitDetector:
    def __init__(self, threshold=500, min_gap=10):
        self.threshold = threshold
        self.min_gap = min_gap  # Minimum samples between detections
        self.last_detection = 0  # Sample count since last detection
        self.last_state = False  # True if above threshold
        self.bits = []  # Detected bits
        self.timestamps = []  # Timestamps of detections
        self.samples_since_last = 0
        self.detection_count = 0

    def reset(self):
        """Reset the detector state"""
        self.last_detection = 0
        self.last_state = False
        self.bits = []
        self.timestamps = []
        self.samples_since_last = 0
        self.detection_count = 0

    def update(self, value, timestamp):
        """Process new sensor value and return (bit_detected, timestamp) if detection occurs"""
        self.samples_since_last += 1
        current_state = value >= self.threshold

        # Detect falling edge
        if self.last_state and not current_state and self.samples_since_last >= self.min_gap:
            self.samples_since_last = 0
            self.detection_count += 1
            self.bits.append(1)  # Record detection
            self.timestamps.append(timestamp)
            self.last_detection = timestamp
            result = (True, timestamp)
        else:
            result = (False, None)

        self.last_state = current_state
        return result


class ExperimentAutomationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Experiment Automation")
        self.experiment_running = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Create experiment configuration groupbox
        config_group = QGroupBox("Experiment Configuration")
        config_layout = QGridLayout()

        # Spray pattern settings
        config_layout.addWidget(QLabel("Spray Pattern:"), 0, 0)
        self.pattern_input = QLineEdit("1010")  # Default pattern
        self.pattern_input.setPlaceholderText("Enter binary pattern (e.g., 1010)")
        config_layout.addWidget(self.pattern_input, 0, 1)

        # Cycle duration
        config_layout.addWidget(QLabel("Spray Cycle Duration (ms):"), 1, 0)
        self.cycle_duration = QSpinBox()
        self.cycle_duration.setRange(100, 10000)
        self.cycle_duration.setValue(1000)
        config_layout.addWidget(self.cycle_duration, 1, 1)

        # Number of repetitions
        config_layout.addWidget(QLabel("Number of Repetitions:"), 2, 0)
        self.repetitions = QSpinBox()
        self.repetitions.setRange(1, 100)
        self.repetitions.setValue(3)
        config_layout.addWidget(self.repetitions, 2, 1)

        # Delay between repetitions
        config_layout.addWidget(QLabel("Delay Between Repetitions (s):"), 3, 0)
        self.delay_between = QSpinBox()
        self.delay_between.setRange(1, 300)
        self.delay_between.setValue(5)
        config_layout.addWidget(self.delay_between, 3, 1)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Fan configuration
        fan_group = QGroupBox("Fan Configuration")
        fan_layout = QGridLayout()

        # Fan pattern dropdown
        fan_layout.addWidget(QLabel("Fan Pattern:"), 0, 0)
        self.fan_pattern = QComboBox()
        self.fan_pattern.addItems(["Custom", "All On", "All Off", "Alternating"])
        self.fan_pattern.currentTextChanged.connect(self.on_fan_pattern_changed)
        fan_layout.addWidget(self.fan_pattern, 0, 1)

        # Fan speed
        fan_layout.addWidget(QLabel("Fan Speed:"), 1, 0)
        self.fan_speed = QComboBox()
        self.fan_speed.addItems(["Off", "Low", "Medium", "High"])
        fan_layout.addWidget(self.fan_speed, 1, 1)

        # Fan grid label
        fan_layout.addWidget(QLabel("Custom Fan Selection:"), 2, 0, 1, 2)

        # Custom fan grid for selecting individual fans
        self.fan_grid = QGridLayout()
        self.fan_checkboxes = []
        for i in range(4):
            row = []
            for j in range(4):
                checkbox = QCheckBox(f"Fan {i * 4 + j}")  # Added fan numbers for clarity
                checkbox.setChecked(True)  # Default all on
                self.fan_grid.addWidget(checkbox, i, j)
                row.append(checkbox)
            self.fan_checkboxes.append(row)
        fan_layout.addLayout(self.fan_grid, 3, 0, 1, 2)

        fan_group.setLayout(fan_layout)
        layout.addWidget(fan_group)

        # Data collection settings
        data_group = QGroupBox("Data Collection")
        data_layout = QGridLayout()

        # Record data checkbox
        self.record_data = QCheckBox("Record Sensor Data")
        self.record_data.setChecked(True)
        data_layout.addWidget(self.record_data, 0, 0)

        # Save location
        data_layout.addWidget(QLabel("Save Location:"), 1, 0)
        save_layout = QHBoxLayout()
        self.save_path = QLineEdit()
        self.save_path.setText("experiment_data")
        save_layout.addWidget(self.save_path)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_save_location)
        save_layout.addWidget(browse_btn)
        data_layout.addLayout(save_layout, 1, 1)

        data_group.setLayout(data_layout)
        layout.addWidget(data_group)

        # Progress display
        self.progress_group = QGroupBox("Experiment Progress")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        self.status_label = QLabel("Ready to start")
        progress_layout.addWidget(self.status_label)
        self.progress_group.setLayout(progress_layout)
        layout.addWidget(self.progress_group)

        # Control buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Experiment")
        self.start_btn.clicked.connect(self.start_experiment)
        self.stop_btn = QPushButton("Stop Experiment")
        self.stop_btn.clicked.connect(self.stop_experiment)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def on_fan_pattern_changed(self, pattern):
        """Handle fan pattern selection"""
        enable_custom = pattern == "Custom"
        for row in self.fan_checkboxes:
            for checkbox in row:
                checkbox.setEnabled(enable_custom)
                if not enable_custom:
                    checkbox.setChecked(pattern == "All On")

    def browse_save_location(self):
        """Open file dialog to choose save location"""
        path = QFileDialog.getExistingDirectory(self, "Select Save Location")
        if path:
            self.save_path.setText(path)

    def setup_data_recording(self):
        """Setup data recording for the experiment"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_file = open(f"{self.save_path.text()}/experiment_{timestamp}.csv", "w")
        self.data_file.write("timestamp,repetition,sensor,value\n")

    def start_experiment(self):
        """Start the automated experiment with debug logging"""
        self.parent.log_terminal.append("Attempting to start experiment...")

        # Validate inputs
        if not self.validate_inputs():
            self.parent.log_terminal.append("Input validation failed")
            return

        # Check serial connection
        if not self.parent.fan_serial:
            self.parent.log_terminal.append("Error: No serial connection")
            QMessageBox.warning(self, "Error", "No serial connection available")
            return

        try:
            self.experiment_running = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setValue(0)

            # Log experiment settings
            self.parent.log_terminal.append(f"""
    Experiment settings:
    - Pattern: {self.pattern_input.text()}
    - Cycle Duration: {self.cycle_duration.value()}ms
    - Repetitions: {self.repetitions.value()}
    - Delay Between: {self.delay_between.value()}s
    - Fan Pattern: {self.fan_pattern.currentText()}
    - Fan Speed: {self.fan_speed.currentText()}
    """)

            # Setup initial fan configuration
            self.configure_fans()
            self.parent.log_terminal.append("Fans configured")

            # Reset repetition counter
            self.current_repetition = 0

            # Start first repetition with explicit call
            QTimer.singleShot(100, self.run_next_repetition)
            self.parent.log_terminal.append("First repetition scheduled")

        except Exception as e:
            self.parent.log_terminal.append(f"Error starting experiment: {str(e)}")
            self.stop_experiment()
            QMessageBox.warning(self, "Error", f"Failed to start experiment: {str(e)}")

    def run_next_repetition(self):
        """Run the next repetition with improved error handling"""
        try:
            self.parent.log_terminal.append("Running next repetition...")

            if not self.experiment_running:
                self.parent.log_terminal.append("Experiment stopped - not running next repetition")
                return

            if self.current_repetition >= self.repetitions.value():
                self.parent.log_terminal.append("All repetitions complete")
                self.finish_experiment()
                return

            self.current_repetition += 1
            self.parent.log_terminal.append(f"Starting repetition {self.current_repetition}")
            self.status_label.setText(f"Running repetition {self.current_repetition} of {self.repetitions.value()}")
            self.progress_bar.setValue((self.current_repetition - 1) * 100 // self.repetitions.value())

            # Send pattern commands
            pattern = self.pattern_input.text()
            cycle_time = self.cycle_duration.value()

            # Log commands being sent
            self.parent.log_terminal.append(f"Sending pattern command: PATTERN,{pattern}")
            self.parent.fan_serial.write(f"PATTERN,{pattern}\n".encode())

            self.parent.log_terminal.append(f"Sending cycle command: CYCLE,{cycle_time}")
            self.parent.fan_serial.write(f"CYCLE,{cycle_time}\n".encode())

            # Calculate timings
            pattern_time = len(pattern) * cycle_time  # Total time for pattern
            delay_time = self.delay_between.value() * 1000  # Delay in ms
            total_time = pattern_time + delay_time

            # Schedule pattern stop and next repetition
            self.parent.log_terminal.append(f"Scheduling pattern stop in {pattern_time}ms")
            QTimer.singleShot(pattern_time, lambda: self.stop_current_pattern())

            self.parent.log_terminal.append(f"Scheduling next repetition in {total_time}ms")
            QTimer.singleShot(total_time, lambda: self.run_next_repetition())

        except Exception as e:
            self.parent.log_terminal.append(f"Error in run_next_repetition: {str(e)}")
            self.stop_experiment()
            QMessageBox.warning(self, "Error", f"Failed during repetition: {str(e)}")

    def validate_inputs(self):
        """Validate all experiment inputs with detailed feedback"""
        self.parent.log_terminal.append("Validating inputs...")

        pattern = self.pattern_input.text()
        if not pattern:
            self.parent.log_terminal.append("Error: Empty pattern")
            QMessageBox.warning(self, "Invalid Input", "Pattern cannot be empty")
            return False

        if not all(c in '01' for c in pattern):
            self.parent.log_terminal.append("Error: Invalid pattern characters")
            QMessageBox.warning(self, "Invalid Input", "Pattern must contain only 0s and 1s")
            return False

        if self.cycle_duration.value() < 100:
            self.parent.log_terminal.append("Error: Cycle duration too short")
            QMessageBox.warning(self, "Invalid Input", "Cycle duration must be at least 100ms")
            return False

        self.parent.log_terminal.append("Input validation passed")
        return True

    def stop_current_pattern(self):
        """Stop the current pattern with logging"""
        try:
            if self.experiment_running and self.parent.fan_serial:
                self.parent.log_terminal.append("Stopping current pattern")
                self.parent.fan_serial.write(b"STOP\n")
                self.parent.log_terminal.append("Pattern stopped")
        except Exception as e:
            self.parent.log_terminal.append(f"Error stopping pattern: {str(e)}")

    def configure_fans(self):
        """Configure fans with logging"""
        try:
            pattern = self.fan_pattern.currentText()
            speed = self.fan_speed.currentIndex()
            self.parent.log_terminal.append(f"Configuring fans - Pattern: {pattern}, Speed: {speed}")

            if pattern == "Custom":
                for i in range(4):
                    for j in range(4):
                        fan_num = i * 4 + j
                        if self.fan_checkboxes[i][j].isChecked():
                            self.parent.queue_fan_command(fan_num, speed)
                            self.parent.log_terminal.append(f"Setting fan {fan_num} to speed {speed}")
                        else:
                            self.parent.queue_fan_command(fan_num, 0)
                            self.parent.log_terminal.append(f"Turning off fan {fan_num}")
            else:
                for fan_num in range(16):
                    fan_speed = speed if pattern == "All On" else 0
                    self.parent.queue_fan_command(fan_num, fan_speed)
                    self.parent.log_terminal.append(f"Setting fan {fan_num} to speed {fan_speed}")

            self.parent.process_fan_commands()
            self.parent.log_terminal.append("Fan configuration complete")
        except Exception as e:
            self.parent.log_terminal.append(f"Error configuring fans: {str(e)}")

    def stop_experiment(self):
        """Stop the current experiment and cleanup"""
        self.experiment_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Experiment stopped")

        # Stop sprayer
        if self.parent.fan_serial:
            try:
                self.parent.fan_serial.write(b"STOP\n")
                self.parent.log_terminal.append("Experiment stopped - sprayer deactivated")
            except Exception as e:
                self.parent.log_terminal.append(f"Error stopping sprayer: {str(e)}")

    def finish_experiment(self):
        """Clean up after experiment completion"""
        self.experiment_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.status_label.setText("Experiment completed")

        if hasattr(self, 'data_file'):
            self.data_file.close()

    def closeEvent(self, event):
        """Handle dialog close"""
        if self.experiment_running:
            self.stop_experiment()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set dark theme
    app.setStyle('Fusion')
    window = SensorArrayGUI()
    window.show()
    sys.exit(app.exec_())
