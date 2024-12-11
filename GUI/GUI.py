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

        self.setWindowTitle("Fan Array Control Interface v.1.01x")
        self.setGeometry(100, 100, 1600, 1000)

        # Initialize variables first
        self.fan_serial = None
        self.sensor_serial = None
        self.pattern_delay = 0.1
        self.start_time = time.time()
        self.sensor_plots = []

        # Initialize threshold spinboxes first
        self.threshold_spins = {}
        for i in range(32):
            spin = QSpinBox()
            spin.setRange(0, 1023)
            spin.setValue(350)  # Default value
            self.threshold_spins[i] = spin

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
        self.SMOOTHING_WINDOW = 10
        self.SMOOTHED_SENSORS = set(range(0, 32))  # Both multiplexer sensors are smoothed
        self.bit_detectors = {}
        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.update_sensor_data)
        self.sensor_timer.start(50)  # Poll every 50ms
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

        # record data
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
        #left_layout.addWidget(detection_panel)

        # Create sensor plots list before creating tabs
        self.sensor_plots = []

        # Create tab widget for multiplexer plots
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_mux_panel(0), "Multiplexer 1 (S1-S16)")
        self.tab_widget.addTab(self.create_mux_panel(1), "Multiplexer 2 (S17-S32)")
        self.tab_widget.addTab(detection_panel, "Threshold Settings")
        # Add panels to main layout
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(self.tab_widget, stretch=2)

        # Setup timers
        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.update_sensor_data)
        self.sensor_timer.start(200)

        self.pattern_timer = QTimer()
        self.pattern_timer.timeout.connect(self.update_fan_pattern)
        self.pattern_timer.start(1000)

        # Log startup
        self.log_terminal.append("Application initialized")

    def smooth_value(self, values):
        """Calculate moving average of the last n values"""
        return sum(values) / len(values) if values else 0

    def update_sensor_threshold(self, sensor_index, value):
        """Update threshold for a specific sensor"""
        try:
            plot = self.sensor_plots[sensor_index]
            plot['threshold_line'].setPos(value)
            if hasattr(self, 'bit_detectors') and sensor_index in self.bit_detectors:
                self.bit_detectors[sensor_index].threshold = value
        except Exception as e:
            self.log_terminal.append(f"Error updating threshold for sensor {sensor_index + 1}: {str(e)}")
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

    def calculate_auto_threshold_mux(self, mux_index):
        """Calculate thresholds automatically for one multiplexer"""
        start_idx = mux_index * 16
        end_idx = start_idx + 16

        for i in range(start_idx, end_idx):
            plot = self.sensor_plots[i]
            if plot['data']['y']:
                # Calculate threshold based on data
                values = plot['data']['y']
                mean = np.mean(values)
                std = np.std(values)
                threshold = int(mean + 2 * std)  # 2 sigma threshold

                # Update the spinbox and threshold line
                self.threshold_spins[i].setValue(threshold)

                # Log the adjustment
                self.log_terminal.append(f"Auto threshold S{i + 1}: {threshold}")

    def calculate_auto_threshold_all(self):
        """Calculate thresholds automatically for all sensors"""
        for i in range(32):
            plot = self.sensor_plots[i]
            if plot['data']['y']:
                values = plot['data']['y']
                mean = np.mean(values)
                std = np.std(values)
                threshold = int(mean + 2 * std)
                self.threshold_spins[i].setValue(threshold)
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
            self.recording_start_time = time.time()
            self.record_end_time = self.recording_start_time + self.record_duration.value()

            # Update UI
            self.record_btn.setText("Stop Recording")
            self.record_duration.setEnabled(False)
            self.log_terminal.append(f"Started recording for {self.record_duration.value()} seconds")

            # Start recording timer
            self.recording_timer = QTimer()
            self.recording_timer.timeout.connect(self.record_data_point)
            self.recording_timer.start(100)  # Record every 100ms

            # Schedule recording stop
            QTimer.singleShot(self.record_duration.value() * 1000, self.stop_recording)

        except Exception as e:
            self.log_terminal.append(f"Error starting recording: {str(e)}")
            self.stop_recording()

    def record_data_point(self):
        """Record a single data point for all sensors"""
        try:
            if not hasattr(self, 'recording_active') or not self.recording_active:
                return

            current_time = datetime.now()
            elapsed_time = time.time() - self.recording_start_time

            # Check if we've reached the recording duration
            if elapsed_time >= self.record_duration.value():
                self.stop_recording()
                return

            # Record data from all sensors
            for sensor_id, plot in enumerate(self.sensor_plots):
                if plot['data']['y']:  # Check if we have any data for this sensor
                    value = plot['data']['y'][-1]  # Get the most recent value
                    self.csv_writer.writerow([
                        current_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                        f"{elapsed_time:.3f}",
                        sensor_id + 1,
                        value
                    ])

            # Ensure data is written to disk
            self.data_file.flush()

            # Update progress bar if we have one
            if hasattr(self, 'progress_bar'):
                progress = (elapsed_time / self.record_duration.value()) * 100
                self.progress_bar.setValue(int(progress))

        except Exception as e:
            self.log_terminal.append(f"Error recording data point: {str(e)}")
            self.stop_recording()

    def stop_recording(self):
        """Stop recording sensor data"""
        try:
            if hasattr(self, 'recording_active') and self.recording_active:
                self.recording_active = False

                # Stop the recording timer
                if hasattr(self, 'recording_timer') and self.recording_timer.isActive():
                    self.recording_timer.stop()

                # Close the data file
                if hasattr(self, 'data_file') and self.data_file:
                    self.data_file.close()
                    self.data_file = None

                # Update UI
                self.record_btn.setText("Record Data")
                self.record_duration.setEnabled(True)
                self.log_terminal.append("Recording stopped")

                # Reset progress bar if we have one
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setValue(0)

        except Exception as e:
            self.log_terminal.append(f"Error stopping recording: {str(e)}")

    def create_mux_panel(self, mux_index):
        """Create a panel with corrected threshold lines"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Add MUX info header
        header = QHBoxLayout()
        header.addWidget(QLabel(f"Multiplexer {mux_index + 1} Sensors"))
        layout.addLayout(header)

        plot_grid = QGridLayout()
        base_sensor = mux_index * 16

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

            for ax in ['left', 'bottom']:
                plot_widget.getAxis(ax).setPen('k')
                plot_widget.getAxis(ax).setTextPen('k')

            plot_widget.setYRange(0, 1023, padding=0.1)
            plot_widget.setXRange(0, 10, padding=0.1)

            # Create main curve with appropriate width
            curve = plot_widget.plot(pen=pg.mkPen('b', width=2))

            # Create threshold line properly
            threshold_value = self.threshold_spins[sensor_num].value()
            threshold_line = pg.InfiniteLine(
                pos=threshold_value,
                angle=0,
                movable=False,
                pen=pg.mkPen('r', style=Qt.DashLine, width=2)
            )
            plot_widget.addItem(threshold_line)

            # Create a more direct connection for threshold updates
            def make_threshold_updater(line, spin):
                def update_threshold():
                    line.setPos(spin.value())

                return update_threshold

            self.threshold_spins[sensor_num].valueChanged.connect(
                make_threshold_updater(threshold_line, self.threshold_spins[sensor_num])
            )

            plot_grid.addWidget(plot_widget, row, col)

            self.sensor_plots.append({
                'widget': plot_widget,
                'curve': curve,
                'threshold_line': threshold_line,
                'data': {'x': [], 'y': []},
                'start_time': None,
                'value_buffer': []  # Add buffer for smoothing
            })

        layout.addLayout(plot_grid)

        # Control buttons
        control_row = QHBoxLayout()

        auto_scale_btn = QPushButton("Auto Scale")
        auto_scale_btn.clicked.connect(lambda: self.auto_scale_mux(mux_index))
        control_row.addWidget(auto_scale_btn)

        reset_view_btn = QPushButton("Reset View (10s)")
        reset_view_btn.clicked.connect(lambda: self.reset_mux_view(mux_index))
        control_row.addWidget(reset_view_btn)

        # Window size control
        window_layout = QHBoxLayout()
        window_layout.addWidget(QLabel("Window:"))

        window_spin = QSpinBox()
        window_spin.setRange(1, 60)
        window_spin.setValue(5)
        window_spin.setSuffix("s")
        window_layout.addWidget(window_spin)

        set_window_btn = QPushButton("Set Window")
        set_window_btn.clicked.connect(
            lambda: self.set_window_size_mux(mux_index, window_spin.value())
        )
        window_layout.addWidget(set_window_btn)

        control_row.addLayout(window_layout)

        layout.addLayout(control_row)
        return panel

    def set_window_size_mux(self, mux_index, duration):
        """Set a fixed window size for all plots in a multiplexer"""
        start_idx = mux_index * 16
        for i in range(16):
            plot = self.sensor_plots[start_idx + i]
            plot['window_size'] = duration  # Store the window size
            if len(plot['data']['x']) > 0:
                latest_time = plot['data']['x'][-1]
                # Set fixed window size
                plot['widget'].setXRange(0, duration, padding=0)
    def quick_view_mux(self, mux_index, duration):
        """Set view to show last N seconds for all plots in a multiplexer"""
        start_idx = mux_index * 16
        for i in range(16):
            plot = self.sensor_plots[start_idx + i]
            if len(plot['data']['x']) > 0:
                latest_time = plot['data']['x'][-1]
                plot['widget'].setXRange(max(0, latest_time - duration), latest_time)

    def auto_scale_mux(self, mux_index):
        """Auto-scale each plot individually based on its own data"""
        start_idx = mux_index * 16
        for i in range(16):
            plot = self.sensor_plots[start_idx + i]
            if plot['data']['y']:
                # Get the min and max values for this sensor
                min_val = min(plot['data']['y'])
                max_val = max(plot['data']['y'])

                # Calculate range and add 10% padding to the top
                value_range = max_val - min_val
                top_padding = value_range * 0.1

                # Set Y range from min value to max value plus 10%
                plot['widget'].setYRange(
                    min_val,
                    max_val + top_padding,
                    padding=0
                )

                # Log the adjustment for debugging
                sensor_num = start_idx + i + 1
                self.log_terminal.append(
                    f"Auto-scaled S{sensor_num} - Range: {min_val:.1f} to {max_val:.1f}"
                )

    def setup_bit_detectors(self):
        """Initialize bit detectors with individual thresholds"""
        for i in range(32):
            threshold = (self.threshold_spins[i].value()
                         if hasattr(self, 'threshold_spins') and i in self.threshold_spins
                         else 250)  # Default value
            self.bit_detectors[i] = BitDetector(threshold=threshold)
    def reset_mux_view(self, mux_index):
        """Reset view and remove fixed window size"""
        start_idx = mux_index * 16
        for i in range(16):
            plot = self.sensor_plots[start_idx + i]
            # Remove fixed window size
            if 'window_size' in plot:
                del plot['window_size']
            # Reset view
            plot['widget'].setYRange(0, 1023, padding=0.1)
            if len(plot['data']['x']) > 0:
                latest_time = plot['data']['x'][-1]
                plot['widget'].setXRange(max(0, latest_time - 10), latest_time)

    def update_sensor_data(self):
        """Update sensor data with improved data format handling"""
        if not self.sensor_serial:
            if not hasattr(self, '_no_serial_logged'):
                self.log_terminal.append("No sensor serial connection available")
                self._no_serial_logged = True
            return

        try:
            if self.sensor_serial.in_waiting:
                line = self.sensor_serial.readline().decode(errors='ignore').strip()

                # Log raw data occasionally for debugging
                if random.random() < 0.01:  # Log ~1% of data for debugging
                    self.log_terminal.append(f"Raw data: {line}")

                # Check if it's a valid data line (starts with $)
                if line.startswith('$'):
                    try:
                        # Split the data
                        data_parts = line[1:].split(',')  # Remove $ and split

                        if len(data_parts) < 33:  # timestamp + 32 sensors
                            self.log_terminal.append(f"Invalid data format (too few parts): {line}")
                            return

                        # Get timestamp
                        timestamp = float(data_parts[0]) / 1000.0  # Convert to seconds

                        # Process sensors in order (first 16 are MUX1, next 16 are MUX2)
                        for i in range(32):
                            try:
                                value = float(data_parts[i + 1])  # +1 to skip timestamp
                                self.update_plot(i, timestamp, value)
                            except ValueError:
                                self.log_terminal.append(f"Error parsing sensor {i + 1} value: {data_parts[i + 1]}")
                            except IndexError:
                                self.log_terminal.append(f"Missing data for sensor {i + 1}")

                    except Exception as e:
                        self.log_terminal.append(f"Error processing data line: {str(e)}")

        except Exception as e:
            if not hasattr(self, '_serial_errors'):
                self._serial_errors = set()
            error_key = str(e)
            if error_key not in self._serial_errors:
                self.log_terminal.append(f"Serial read error: {str(e)}")
                self._serial_errors.add(error_key)

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
        """Create detection settings panel with per-sensor thresholds"""
        detection_panel = QFrame()
        detection_panel.setFrameStyle(QFrame.Panel | QFrame.Raised)
        detection_layout = QVBoxLayout(detection_panel)
        detection_layout.addWidget(QLabel("Detection Settings"))

        # Create tab widget for threshold settings
        threshold_tabs = QTabWidget()

        # Create panels for each multiplexer's thresholds
        for mux_index in range(2):
            mux_panel = QWidget()
            mux_layout = QGridLayout()

            # Create threshold controls for each sensor in this multiplexer
            for i in range(16):
                sensor_num = mux_index * 16 + i
                row = i // 4
                col = i % 4

                # Create group box for each sensor
                sensor_group = QGroupBox(f"S{sensor_num + 1}")
                sensor_layout = QVBoxLayout()

                # Threshold spinbox
                spin = QSpinBox()
                spin.setRange(0, 1023)
                # Initialize with a value close to the current sensor reading if available
                if sensor_num in self.sensor_plots and self.sensor_plots[sensor_num]['data']['y']:
                    current_val = self.sensor_plots[sensor_num]['data']['y'][-1]
                    spin.setValue(int(current_val * 0.9))  # Set to 90% of current value
                else:
                    spin.setValue(500)  # Default value

                self.threshold_spins[sensor_num] = spin
                spin.valueChanged.connect(lambda v, s=sensor_num: self.update_sensor_threshold(s, v))
                sensor_layout.addWidget(spin)

                sensor_group.setLayout(sensor_layout)
                mux_layout.addWidget(sensor_group, row, col)

            mux_panel.setLayout(mux_layout)
            threshold_tabs.addTab(mux_panel, f"MUX{mux_index + 1} Thresholds")

        detection_layout.addWidget(threshold_tabs)

        # Auto threshold controls
        auto_threshold_layout = QHBoxLayout()

        # Auto threshold for visible MUX
        auto_visible_btn = QPushButton("Auto Threshold Visible MUX")
        auto_visible_btn.clicked.connect(lambda: self.calculate_auto_threshold_mux(threshold_tabs.currentIndex()))
        auto_visible_btn.setToolTip("Set thresholds for currently visible multiplexer based on sensor readings")
        auto_threshold_layout.addWidget(auto_visible_btn)

        # Auto threshold all
        auto_all_btn = QPushButton("Auto Threshold All")
        auto_all_btn.clicked.connect(self.calculate_auto_threshold_all)
        auto_all_btn.setToolTip("Set thresholds for all sensors based on their readings")
        auto_threshold_layout.addWidget(auto_all_btn)

        detection_layout.addLayout(auto_threshold_layout)

        return detection_panel

    def calculate_auto_threshold_mux(self, mux_index):
        """Calculate appropriate thresholds for one multiplexer automatically"""
        start_idx = mux_index * 16
        end_idx = start_idx + 16

        for i in range(start_idx, end_idx):
            plot = self.sensor_plots[i]
            if plot['data']['y']:
                # Get recent values
                recent_values = plot['data']['y'][-100:]  # Last 100 readings
                if recent_values:
                    mean = np.mean(recent_values)
                    std = np.std(recent_values)

                    # Set threshold to mean + 1 standard deviation
                    threshold = int(mean + std)

                    # Update spinbox and threshold line
                    self.threshold_spins[i].setValue(threshold)
                    plot['threshold_line'].setPos(threshold)

                    # Log the adjustment
                    self.log_terminal.append(f"Auto threshold S{i + 1}: {threshold} (mean: {mean:.1f}, std: {std:.1f})")

    def calculate_auto_threshold_all(self):
        """Calculate appropriate thresholds for all sensors automatically"""
        for i in range(32):
            plot = self.sensor_plots[i]
            if plot['data']['y']:
                recent_values = plot['data']['y'][-100:]
                if recent_values:
                    mean = np.mean(recent_values)
                    std = np.std(recent_values)
                    threshold = int(mean + std)
                    self.threshold_spins[i].setValue(threshold)
                    plot['threshold_line'].setPos(threshold)
                    self.log_terminal.append(f"Auto threshold S{i + 1}: {threshold}")
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

    def connect_devices(self, fan_port, sensor_port, fan_baud=115200, sensor_baud=115200):
        """Connect to single Arduino handling both fans and sensors"""
        # Close existing connection if any
        if self.fan_serial:
            try:
                self.fan_serial.close()
            except:
                pass
            self.fan_serial = None
            self.sensor_serial = None  # Clear both since they're the same device

        # Connect to Arduino
        if fan_port and fan_port != "No ports found":
            try:
                self.fan_serial = serial.Serial(
                    port=fan_port,
                    baudrate=fan_baud,
                    timeout=0.1
                )
                time.sleep(2)  # Wait for Arduino reset
                self.sensor_serial = self.fan_serial  # Use same connection for sensors
                self.log_terminal.append(f"Connected to Arduino controller on {fan_port}")

                # Verify we're receiving data
                timeout = time.time() + 5  # 5 second timeout
                data_received = False
                while time.time() < timeout and not data_received:
                    if self.fan_serial.in_waiting:
                        line = self.fan_serial.readline().decode(errors='ignore').strip()
                        self.log_terminal.append(f"First data received: {line}")
                        data_received = True
                    time.sleep(0.1)

                if not data_received:
                    self.log_terminal.append("Warning: No initial data received")

            except Exception as e:
                self.log_terminal.append(f"Controller connection error: {str(e)}")
                self.fan_serial = None
                self.sensor_serial = None
                QMessageBox.warning(self, "Connection Error",
                                    f"Failed to connect to controller: {str(e)}")
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
        """Update plot with fixed window size support and proper smoothing"""
        try:
            plot = self.sensor_plots[plot_index]

            # Initialize start_time if not set
            if plot['start_time'] is None:
                plot['start_time'] = timestamp

            # Calculate relative time from start
            relative_time = timestamp - plot['start_time']

            # Apply smoothing using the buffer
            if not hasattr(plot, 'value_buffer'):
                plot['value_buffer'] = []

            plot['value_buffer'].append(value)
            if len(plot['value_buffer']) > self.SMOOTHING_WINDOW:
                plot['value_buffer'].pop(0)

            # Calculate smoothed value
            if len(plot['value_buffer']) >= 3:  # Only smooth if we have enough data points
                smoothed_value = sum(plot['value_buffer']) / len(plot['value_buffer'])
            else:
                smoothed_value = value

            # Store new data point
            plot['data']['x'].append(relative_time)
            plot['data']['y'].append(smoothed_value)

            # If we have a fixed window size, adjust the data storage
            if 'window_size' in plot and plot['window_size']:
                window = plot['window_size']

                # Keep only data within the window
                while len(plot['data']['x']) > 0 and plot['data']['x'][-1] - plot['data']['x'][0] > window:
                    plot['data']['x'].pop(0)
                    plot['data']['y'].pop(0)

                # Shift all times to keep the window starting at 0
                if len(plot['data']['x']) > 0:
                    time_shift = plot['data']['x'][-1] - window
                    if time_shift > 0:
                        plot['data']['x'] = [t - time_shift for t in plot['data']['x']]
                        plot['start_time'] += time_shift

            # Update main data curve
            plot['curve'].setData(plot['data']['x'], plot['data']['y'])

            # Update threshold line with the correct sensor's threshold value
            plot['threshold_line'].setPos(self.threshold_spins[plot_index].value())

            # If we have a fixed window size, maintain it
            if 'window_size' in plot and plot['window_size']:
                plot['widget'].setXRange(0, plot['window_size'], padding=0)

            # Auto-scale Y axis if enabled
            if plot['widget'].getViewBox().state['autoRange'][1]:
                if plot['data']['y']:
                    min_val = min(plot['data']['y'])
                    max_val = max(plot['data']['y'])
                    value_range = max_val - min_val
                    top_padding = value_range * 0.1
                    plot['widget'].setYRange(min_val, max_val + top_padding, padding=0)

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
        """Start the spray pattern sequence with debug output"""
        pattern = self.pattern_input.text()

        # Validate pattern
        if not pattern or not all(bit in '01' for bit in pattern):
            self.log_terminal.append("Invalid pattern. Please use only 0s and 1s.")
            return

        if not self.fan_serial:
            self.log_terminal.append("Fan controller not connected.")
            return

        try:
            # Send timing configuration
            cycle_time = self.cycle_duration.value()
            config_command = f"CONFIG,{cycle_time}\n"
            self.fan_serial.write(config_command.encode())
            self.log_terminal.append(f"Sent config: {config_command.strip()}")

            # Small delay between commands
            time.sleep(0.1)

            # Send pattern
            pattern_command = f"PATTERN,{pattern}\n"
            self.fan_serial.write(pattern_command.encode())
            self.log_terminal.append(f"Sent pattern: {pattern_command.strip()}")

            # Update UI
            self.start_pattern_btn.setEnabled(False)
            self.stop_pattern_btn.setEnabled(True)
            self.pattern_input.setEnabled(False)
            self.cycle_duration.setEnabled(False)
            self.spray_status.setText("Status: Running Pattern")

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
    def __init__(self, threshold=500, min_gap=10, window_size=5):
        self.threshold = threshold
        self.min_gap = min_gap
        self.window_size = window_size
        self.last_detection = 0
        self.last_state = False
        self.bits = []
        self.timestamps = []
        self.samples_since_last = 0
        self.detection_count = 0
        self.buffer = []  # Buffer for moving average
        self.baseline = None
        self.baseline_samples = []
        self.baseline_window = 50  # Samples to establish baseline
        self.trigger_threshold = 0.15  # 15% change from baseline triggers detection

    def reset(self):
        """Reset the detector state"""
        self.last_detection = 0
        self.last_state = False
        self.bits = []
        self.timestamps = []
        self.samples_since_last = 0
        self.detection_count = 0
        self.buffer = []
        self.baseline = None
        self.baseline_samples = []

    def calculate_baseline(self, value):
        """Establish or update the baseline"""
        self.baseline_samples.append(value)
        if len(self.baseline_samples) > self.baseline_window:
            self.baseline_samples.pop(0)
        self.baseline = sum(self.baseline_samples) / len(self.baseline_samples)

    def smooth_value(self, value):
        """Apply moving average smoothing"""
        self.buffer.append(value)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
        return sum(self.buffer) / len(self.buffer)

    def update(self, raw_value, timestamp):
        """Process new sensor value with improved detection"""
        # Initialize or update baseline
        if self.baseline is None or len(self.baseline_samples) < self.baseline_window:
            self.calculate_baseline(raw_value)
            return False, None

        # Apply smoothing
        smoothed_value = self.smooth_value(raw_value)

        # Calculate percentage change from baseline
        if self.baseline > 0:
            percent_change = abs(smoothed_value - self.baseline) / self.baseline
        else:
            percent_change = 0

        # Update baseline during non-detection periods
        if percent_change < self.trigger_threshold:
            self.calculate_baseline(raw_value)

        self.samples_since_last += 1

        # Detect significant changes
        current_state = percent_change >= self.trigger_threshold

        # Detect falling edge (spray detection)
        if self.last_state and not current_state and self.samples_since_last >= self.min_gap:
            self.samples_since_last = 0
            self.detection_count += 1
            self.bits.append(1)
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
        progress_group = QGroupBox("Experiment Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to start")
        progress_layout.addWidget(self.status_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

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

    def start_experiment(self):
        """Start the automated experiment"""
        try:
            # Validate inputs
            pattern = self.pattern_input.text()
            if not pattern or not all(c in '01' for c in pattern):
                QMessageBox.warning(self, "Invalid Input", "Pattern must contain only 0s and 1s")
                return

            if self.cycle_duration.value() < 100:
                QMessageBox.warning(self, "Invalid Input", "Cycle duration must be at least 100ms")
                return

            if not self.parent.fan_serial:
                QMessageBox.warning(self, "Error", "No serial connection available")
                return

            # Create experiment directory if needed
            save_dir = self.save_path.text()
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            # Setup data file in experiment directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.data_filename = f"{save_dir}/experiment_{timestamp}.csv"
            self.data_file = open(self.data_filename, 'w', newline='')
            self.csv_writer = csv.writer(self.data_file)
            self.csv_writer.writerow(['Timestamp', 'Repetition', 'Sensor_ID', 'Value'])

            # Initialize experiment state
            self.experiment_running = True
            self.current_repetition = 0

            # Update UI
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("Starting experiment...")

            # Start first repetition
            self.run_next_repetition()

        except Exception as e:
            self.parent.log_terminal.append(f"Error starting experiment: {str(e)}")
            self.stop_experiment()

    def run_next_repetition(self):
        """Run next repetition of the experiment"""
        try:
            if not self.experiment_running:
                return

            self.current_repetition += 1

            # Check if we've completed all repetitions
            if self.current_repetition > self.repetitions.value():
                self.finish_experiment()
                return

            # Update UI
            self.status_label.setText(f"Running repetition {self.current_repetition} of {self.repetitions.value()}")
            self.progress_bar.setValue(((self.current_repetition - 1) * 100) // self.repetitions.value())

            # Get pattern parameters
            pattern = self.pattern_input.text()
            cycle_time = self.cycle_duration.value()

            if self.parent.fan_serial:
                # Send CONFIG command for sprayer
                self.parent.fan_serial.write(f"CONFIG,{cycle_time}\n".encode())
                time.sleep(0.1)  # Small delay between commands

                # Send PATTERN command
                self.parent.fan_serial.write(f"PATTERN,{pattern}\n".encode())

                # Calculate timings
                pattern_duration = len(pattern) * cycle_time  # Total time for pattern in ms
                delay_time = self.delay_between.value() * 1000  # Convert to ms
                total_time = pattern_duration + delay_time

                # Start recording if enabled
                if self.record_data.isChecked():
                    self.record_timer = QTimer()
                    self.record_timer.timeout.connect(self.record_sensor_data)
                    self.record_timer.start(100)  # Record every 100ms

                # Schedule pattern stop and next repetition
                QTimer.singleShot(pattern_duration, self.stop_current_pattern)
                QTimer.singleShot(total_time, self.run_next_repetition)

        except Exception as e:
            self.parent.log_terminal.append(f"Error in repetition: {str(e)}")
            self.stop_experiment()

    def record_sensor_data(self):
        """Record current sensor data"""
        try:
            if not hasattr(self, 'data_file') or self.data_file is None:
                return

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

            # Record data from all sensors
            for sensor_id in range(32):
                if sensor_id < len(self.parent.sensor_plots):
                    plot = self.parent.sensor_plots[sensor_id]
                    if plot['data']['y']:
                        value = plot['data']['y'][-1]
                        self.csv_writer.writerow([
                            current_time,
                            self.current_repetition,
                            sensor_id + 1,
                            value
                        ])

            # Ensure data is written to disk
            self.data_file.flush()

        except Exception as e:
            self.parent.log_terminal.append(f"Error recording data: {str(e)}")

    def browse_save_location(self):
        """Open file dialog to choose save location"""
        path = QFileDialog.getExistingDirectory(self, "Select Save Location")
        if path:
            self.save_path.setText(path)

    def stop_current_pattern(self):
        """Stop only the spray pattern"""
        if self.experiment_running and self.parent.fan_serial:
            self.parent.fan_serial.write(b"STOP\n")

    def stop_experiment(self):
        """Stop the experiment"""
        self.experiment_running = False

        # Stop pattern
        if self.parent.fan_serial:
            self.parent.fan_serial.write(b"STOP\n")

        # Stop recording
        if hasattr(self, 'record_timer') and self.record_timer.isActive():
            self.record_timer.stop()

        # Close data file
        if hasattr(self, 'data_file') and self.data_file is not None:
            self.data_file.close()
            self.data_file = None

        # Update UI
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Experiment stopped")

    def finish_experiment(self):
        """Complete the experiment"""
        self.experiment_running = False

        # Stop recording
        if hasattr(self, 'record_timer') and self.record_timer.isActive():
            self.record_timer.stop()

        # Close data file
        if hasattr(self, 'data_file') and self.data_file is not None:
            self.data_file.close()
            self.data_file = None

        # Update UI
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.status_label.setText("Experiment completed")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set dark theme
    app.setStyle('Fusion')
    window = SensorArrayGUI()
    window.show()
    sys.exit(app.exec_())