import sys
import serial
import time
from serial.tools import list_ports
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QPushButton, QLabel,
                             QComboBox, QTextEdit, QFrame, QMessageBox,
                             QDialog, QLineEdit, QGroupBox, QSpinBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette
import pyqtgraph as pg
import random
from scipy.signal import find_peaks
import numpy as np

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
        self.setWindowTitle("Fan Array Control Interface v.0.03")
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

        self.sensor_buffers = {i: [] for i in range(10)}  # Buffer for each sensor
        self.SMOOTHING_WINDOW = 3  # Number of samples to average
        self.SMOOTHED_SENSORS = {6, 7, 8, 9}  # Sensors that need smoothing (A6-A9)
        super().__init__()

        # Then create the rest of the UI
        self.setup_ui()

    def setup_ui(self):
        # Set plot configs
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Left panel for fan controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Add fan control panel
        fan_panel = self.create_fan_panel()
        left_layout.addWidget(fan_panel)

        # Add sprayer panel
        sprayer_panel = self.create_sprayer_panel()
        left_layout.addWidget(sprayer_panel)

        # Add log terminal
        self.log_terminal = QTextEdit()
        self.log_terminal.setReadOnly(True)
        self.log_terminal.setMaximumHeight(200)
        left_layout.addWidget(self.log_terminal)

        # In the setup_ui method, add this near where you create the log_terminal:
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

        # Create and add the right panel (plots)
        right_panel = self.create_plots()

        # Add panels to main layout
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(right_panel, stretch=2)

        # Setup timers
        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.update_sensor_data)
        self.sensor_timer.start(200)  # Update every 200ms

        self.pattern_timer = QTimer()
        self.pattern_timer.timeout.connect(self.update_fan_pattern)
        self.pattern_timer.start(5000)  # Update every 5 seconds

    def smooth_value(self, values):
        """Calculate moving average of the last n values"""
        return sum(values) / len(values) if values else 0

    def create_plots(self):
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        plot_grid = QGridLayout()
        self.sensor_plots = []

        # Create 8 plots in a 4x2 grid
        for i in range(10):
            row = i // 2  # 4 rows
            col = i % 2  # 2 columns

            plot_widget = pg.PlotWidget()
            plot_widget.setBackground('w')
            plot_widget.setTitle(f'Sensor {i} (Pin {22 + i * 2})')
            plot_widget.setLabel('left', 'Value')
            plot_widget.setLabel('bottom', 'Time (s)')
            plot_widget.showGrid(x=True, y=True)
            plot_widget.getAxis('left').setPen('k')
            plot_widget.getAxis('bottom').setPen('k')
            plot_widget.getAxis('left').setTextPen('k')
            plot_widget.getAxis('bottom').setTextPen('k')

            # Set Y axis range (0 to 1023 for full analog range)
            plot_widget.setYRange(0, 1023)
            plot_widget.setXRange(-30, 0)
            plot_widget.enableAutoRange(axis='y', enable=True)

            curve = plot_widget.plot(pen='b')
            threshold_line = plot_widget.addLine(y=self.threshold_spin.value(),
                                                 pen=pg.mkPen('r', style=Qt.DashLine))
            peaks_scatter = pg.ScatterPlotItem(pen=None, symbol='o',
                                               size=8, brush=pg.mkBrush('g'))
            crossings_scatter = pg.ScatterPlotItem(pen=None, symbol='x',
                                                   size=8, brush=pg.mkBrush('r'))

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

        right_layout.addLayout(plot_grid)
        return right_panel
    def update_sensor_data(self):
        """Update sensor data with smoothing for specific sensors"""
        if not self.sensor_serial:
            if not hasattr(self, '_no_serial_logged'):
                self.log_terminal.append("No sensor serial connection available")
                self._no_serial_logged = True
            return

        try:
            if self.sensor_serial.in_waiting:
                line = self.sensor_serial.readline().decode().strip()

                try:
                    if line.startswith("START") and line.endswith("END"):
                        parts = line.split(',')
                        timestamp = time.time() - self.start_time

                        # Process all sensors
                        for part in parts[2:-1]:  # Skip START, timestamp, and END
                            if ':' in part and part.startswith('S'):
                                try:
                                    sensor_str, value_str = part.split(':')
                                    sensor_num = int(sensor_str.replace('S', '')) - 1
                                    raw_value = float(value_str)

                                    # Add value to buffer
                                    if sensor_num in self.sensor_buffers:
                                        self.sensor_buffers[sensor_num].append(raw_value)
                                        # Keep buffer at smoothing window size
                                        if len(self.sensor_buffers[sensor_num]) > self.SMOOTHING_WINDOW:
                                            self.sensor_buffers[sensor_num].pop(0)

                                    # Apply smoothing for sensors A6-A9
                                    if sensor_num in self.SMOOTHED_SENSORS:
                                        value = self.smooth_value(self.sensor_buffers[sensor_num])
                                    else:
                                        value = raw_value

                                    if 0 <= sensor_num < len(self.sensor_plots):
                                        self.update_plot(sensor_num, timestamp, value)

                                        # Log only occasionally to avoid spam
                                        if timestamp % 5 < 0.1:
                                            if sensor_num in self.SMOOTHED_SENSORS:
                                                self.log_terminal.append(
                                                    f"Sensor {sensor_num + 1}: raw={raw_value:.2f}, "
                                                    f"smoothed={value:.2f}")
                                            elif sensor_num == 0:  # Log sensor 0 as reference
                                                self.log_terminal.append(
                                                    f"Sensor {sensor_num + 1}: value={value:.2f}")

                                except ValueError as ve:
                                    self.log_terminal.append(f"Value error for {sensor_str}: {ve}")

                    elif not line.startswith("Fan"):  # Ignore fan control messages
                        self.log_terminal.append(f"Unknown data format: {line}")

                except Exception as e:
                    self.log_terminal.append(f"Error parsing line: {str(e)}")

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

    def update_plot(self, plot_index, timestamp, value):
        """Helper function to update a single plot with smoothing visualization"""
        try:
            plot = self.sensor_plots[plot_index]

            # Store new data point
            plot['data']['x'].append(timestamp)
            plot['data']['y'].append(value)

            # Keep last 30 seconds of data
            current_time = timestamp
            while plot['data']['x'] and (current_time - plot['data']['x'][0]) > 30:
                plot['data']['x'].pop(0)
                plot['data']['y'].pop(0)

            # Update plot data with different styling for smoothed sensors
            if plot_index in self.SMOOTHED_SENSORS:
                # Use a thicker line for smoothed data
                plot['curve'].setData(
                    plot['data']['x'],
                    plot['data']['y'],
                    pen=pg.mkPen('b', width=2)  # Thicker blue line for smoothed data
                )

                # Update title for smoothed plots (safely)
                if not hasattr(plot['widget'], '_smoothing_indicator'):
                    current_title = plot['widget'].getPlotItem().titleLabel.text
                    plot['widget'].setTitle(f"{current_title} (Smoothed)")
                    try:
                        plot['widget'].getPlotItem().titleLabel.setStyleSheet("color: #0066cc;")
                    except:
                        pass  # If style setting fails, continue without style
                    plot['widget']._smoothing_indicator = True
            else:
                plot['curve'].setData(
                    plot['data']['x'],
                    plot['data']['y'],
                    pen=pg.mkPen('b', width=1)  # Normal line for raw data
                )

            # Auto-scale Y axis with more padding for smoothed sensors
            if len(plot['data']['y']) > 0:
                ymin = min(plot['data']['y'])
                ymax = max(plot['data']['y'])
                padding = (ymax - ymin) * (0.15 if plot_index in self.SMOOTHED_SENSORS else 0.1)
                if padding == 0:  # Handle case where min == max
                    padding = 0.1 * ymax if ymax != 0 else 1.0
                plot['widget'].setYRange(ymin - padding, ymax + padding)

            # Update X axis to show moving 30-second window
            plot['widget'].setXRange(current_time - 30, current_time)

            # Update threshold line position
            plot['threshold_line'].setValue(self.threshold_spin.value())

            # Process peaks and crossings
            self.process_plot_data(plot_index)

        except Exception as e:
            if not hasattr(self, '_plot_errors'):
                self._plot_errors = set()
            error_key = f"{plot_index}:{str(e)}"
            if error_key not in self._plot_errors:
                self.log_terminal.append(f"Plot update error for sensor {plot_index + 1}: {str(e)}")
                self._plot_errors.add(error_key)  # Only log each unique error once



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

    # Add these new methods to your SensorArrayGUI class

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

    import sys
    import serial
    import time
    from serial.tools import list_ports
    import numpy as np
    from datetime import datetime
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                 QHBoxLayout, QGridLayout, QPushButton, QLabel,
                                 QComboBox, QTextEdit, QFrame, QMessageBox,
                                 QDialog, QLineEdit, QGroupBox, QSpinBox)
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QColor, QPalette
    import pyqtgraph as pg
    import random

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
            self.setWindowTitle("Fan Array Control Interface v.0.02")
            self.setGeometry(100, 100, 1600, 1000)

            # Set default background to white for plots
            pg.setConfigOption('background', 'w')
            pg.setConfigOption('foreground', 'k')

            # Initialize serial connections as None
            self.fan_serial = None
            self.sensor_serial = None
            self.pattern_delay = 0.1

            self.threshold_spin = QSpinBox()
            self.threshold_spin.setRange(0, 1023)
            self.threshold_spin.setValue(500)

            # Create main widget and layout
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            main_layout = QHBoxLayout(main_widget)

            # Left panel for fan controls
            left_panel = QWidget()
            left_layout = QVBoxLayout(left_panel)

            # Right panel for graphs
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)

            # Create graph widgets
            self.sensor_plots = []
            plot_grid = QGridLayout()

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
            for i in range(10):
                # Calculate grid position
                row = i // 2  # 4 rows
                col = i % 2  # 2 columns

                # Create plot widget
                plot_widget = pg.PlotWidget()
                plot_widget.setBackground('w')
                plot_widget.setTitle(f'Sensor {i + 1} (Pin {22 + i * 2})')
                plot_widget.setLabel('left', 'Value')
                plot_widget.setLabel('bottom', 'Time (s)')
                plot_widget.showGrid(x=True, y=True)
                plot_widget.getAxis('left').setPen('k')
                plot_widget.getAxis('bottom').setPen('k')
                plot_widget.getAxis('left').setTextPen('k')
                plot_widget.getAxis('bottom').setTextPen('k')

                # Set Y axis range (0 to 1023 for full analog range)
                plot_widget.setYRange(0, 1023)
                # Set X axis range (30 seconds window)
                plot_widget.setXRange(-30, 0)
                # Enable auto-ranging after initial setup
                plot_widget.enableAutoRange(axis='y', enable=True)

                # Create plot data item for main signal
                curve = plot_widget.plot(pen='b')

                # Add threshold line
                threshold_line = plot_widget.addLine(y=self.threshold_spin.value(),
                                                     pen=pg.mkPen('r', style=Qt.DashLine))

                # Add scatter plots for peaks and crossings
                peaks_scatter = pg.ScatterPlotItem(pen=None, symbol='o',
                                                   size=8, brush=pg.mkBrush('g'))
                crossings_scatter = pg.ScatterPlotItem(pen=None, symbol='x',
                                                       size=8, brush=pg.mkBrush('r'))
                plot_widget.addItem(peaks_scatter)
                plot_widget.addItem(crossings_scatter)

                # Add to grid
                plot_grid.addWidget(plot_widget, row, col)

                # Store references
                self.sensor_plots.append({
                    'widget': plot_widget,
                    'curve': curve,
                    'threshold_line': threshold_line,
                    'peaks_scatter': peaks_scatter,
                    'crossings_scatter': crossings_scatter,
                    'data': {'x': [], 'y': []}
                })

            right_layout.addLayout(plot_grid)

            # Fan controls
            self.fan_mode = QComboBox()
            self.fan_mode.addItems(["Random Power", "Custom", "All On", "All Off"])
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
            fan_layout.addWidget(QLabel("Programs:"))
            fan_layout.addWidget(self.fan_mode)
            fan_layout.addLayout(speed_layout)

            # Add fan panel to left layout
            left_layout.addWidget(fan_panel)

            # Sprayer Control Panel
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

            # Cycle duration control
            self.cycle_duration = QSpinBox()
            self.cycle_duration.setRange(100, 60000)  # 100ms to 60 seconds
            self.cycle_duration.setValue(1000)  # Default 1 second
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

            # Add sprayer panel to left layout after fan panel
            left_layout.addWidget(sprayer_panel)

            # Add log terminal
            self.log_terminal = QTextEdit()
            self.log_terminal.setReadOnly(True)
            self.log_terminal.setMaximumHeight(200)
            left_layout.addWidget(self.log_terminal)

            # Add detection settings panel
            detection_panel = QFrame()
            detection_panel.setFrameStyle(QFrame.Panel | QFrame.Raised)
            detection_layout = QVBoxLayout(detection_panel)
            detection_layout.addWidget(QLabel("Detection Settings"))

            # Detection controls
            controls_layout = QGridLayout()

            # Threshold control
            self.threshold_spin = QSpinBox()
            self.threshold_spin.setRange(0, 1023)
            self.threshold_spin.setValue(500)
            self.threshold_spin.valueChanged.connect(self.update_detection_settings)
            controls_layout.addWidget(QLabel("Threshold:"), 0, 0)
            controls_layout.addWidget(self.threshold_spin, 0, 1)

            # Peak height control
            self.peak_height_spin = QSpinBox()
            self.peak_height_spin.setRange(0, 1023)
            self.peak_height_spin.setValue(700)
            self.peak_height_spin.valueChanged.connect(self.update_detection_settings)
            controls_layout.addWidget(QLabel("Peak Height:"), 1, 0)
            controls_layout.addWidget(self.peak_height_spin, 1, 1)

            # Peak distance control
            self.peak_distance_spin = QSpinBox()
            self.peak_distance_spin.setRange(1, 100)
            self.peak_distance_spin.setValue(20)
            self.peak_distance_spin.valueChanged.connect(self.update_detection_settings)
            controls_layout.addWidget(QLabel("Peak Distance:"), 2, 0)
            controls_layout.addWidget(self.peak_distance_spin, 2, 1)

            detection_layout.addLayout(controls_layout)

            # Auto threshold button
            auto_threshold_btn = QPushButton("Auto Threshold")
            auto_threshold_btn.clicked.connect(self.calculate_auto_threshold)
            detection_layout.addWidget(auto_threshold_btn)

            left_layout.addWidget(detection_panel)

            # Right panel for graphs
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)

            # Create graph widgets
            self.sensor_plots = []
            plot_grid = QGridLayout()
            right_layout.addLayout(plot_grid)

            # Add panels to main layout
            main_layout.addWidget(left_panel, stretch=1)
            main_layout.addWidget(right_panel, stretch=2)

            # Setup sensor data collection timer
            self.sensor_timer = QTimer()
            self.sensor_timer.timeout.connect(self.update_sensor_data)
            self.sensor_timer.start(50)  # Update every 50ms

            # Setup pattern timer
            self.pattern_timer = QTimer()
            self.pattern_timer.timeout.connect(self.update_fan_pattern)
            self.pattern_timer.start(5000)  # Update every second

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
            """Improved cleanup on program exit"""
            # Stop all timers
            self.sensor_timer.stop()
            self.pattern_timer.stop()

            # Stop any running pattern
            self.stop_spray_pattern()

            # Clean up fan controller
            if self.fan_serial:
                try:
                    # Turn all fans off
                    for i in range(16):
                        self.fan_serial.write(f"{i},0\n".encode())
                    self.fan_serial.flush()  # Ensure all data is written
                    self.fan_serial.close()
                except Exception as e:
                    self.log_terminal.append(f"Error closing fan serial: {str(e)}")

            # Clean up sensor controller
            if self.sensor_serial:
                try:
                    self.sensor_serial.cancel_read()  # Cancel any pending reads
                    self.sensor_serial.flush()
                    self.sensor_serial.flushInput()
                    self.sensor_serial.flushOutput()
                    self.sensor_serial.close()
                except Exception as e:
                    self.log_terminal.append(f"Error closing sensor serial: {str(e)}")

            event.accept()

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


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set dark theme
    app.setStyle('Fusion')
    window = SensorArrayGUI()
    window.show()
    sys.exit(app.exec_())
