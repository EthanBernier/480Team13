import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QPushButton, QLabel,
<<<<<<< Updated upstream
                             QComboBox, QTextEdit, QFrame)
from PyQt5.QtCore import Qt, QTimer
import random

=======
                             QComboBox, QTextEdit, QFrame, QMessageBox,
                             QDialog, QLineEdit, QGroupBox, QSpinBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette
import pyqtgraph as pg
import random
import scipy

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
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
        self.setWindowTitle("Sensor Array Interface v.0.01")
        self.setGeometry(100, 100, 1200, 800)
=======
        self.setWindowTitle("Fan Array Control Interface v.0.02")
        self.setGeometry(100, 100, 1600, 1000)

        # Set default background to white for plots
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        # Initialize serial connections as None
        self.fan_serial = None
        self.sensor_serial = None
        self.pattern_delay = 0.1
>>>>>>> Stashed changes

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Create top section with fan control and sensor array
        top_section = QWidget()
        top_layout = QHBoxLayout(top_section)

        # Fan Control Panel
        fan_panel = QFrame()
        fan_panel.setFrameStyle(QFrame.Panel | QFrame.Raised)
        fan_layout = QVBoxLayout(fan_panel)

        # Fan array (4x4 grid of buttons)
        fan_grid = QGridLayout()
        self.fan_buttons = []
        for i in range(4):
            row = []
            for j in range(4):
                btn = QPushButton()
                btn.setCheckable(True)
                btn.setMinimumSize(50, 50)
                btn.clicked.connect(self.toggle_fan)
                fan_grid.addWidget(btn, i, j)
                row.append(btn)
            self.fan_buttons.append(row)

<<<<<<< Updated upstream
        # Fan control dropdown and buttons
        self.fan_mode = QComboBox()
        self.fan_mode.addItems(["Random Power", "Waves", "Custom", "All on", "All off"])
=======
        # Fan controls
        self.fan_mode = QComboBox()
        self.fan_mode.addItems(["Random Power" , "Custom", "All On", "All Off"])
>>>>>>> Stashed changes
        self.fan_mode.currentTextChanged.connect(self.change_fan_mode)

        fan_layout.addWidget(QLabel("Fan Control Array"))
        fan_layout.addLayout(fan_grid)
        fan_layout.addWidget(QLabel("Programs:"))
        fan_layout.addWidget(self.fan_mode)

        # Sensor Array Panel
        sensor_panel = QFrame()
        sensor_panel.setFrameStyle(QFrame.Panel | QFrame.Raised)
        sensor_layout = QVBoxLayout(sensor_panel)

<<<<<<< Updated upstream
        # Sensor array (4x4 grid of labels)
        sensor_grid = QGridLayout()
        self.sensor_labels = []
=======
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

>>>>>>> Stashed changes
        for i in range(4):
            row = []
            for j in range(4):
<<<<<<< Updated upstream
                label = QLabel()
                label.setMinimumSize(50, 50)
                label.setStyleSheet("background-color: gray;")
                label.setAlignment(Qt.AlignCenter)
                sensor_grid.addWidget(label, i, j)
                row.append(label)
            self.sensor_labels.append(row)
=======
                # Create plot widget
                plot_widget = pg.PlotWidget()
                plot_widget.setBackground('w')
                plot_widget.setTitle(f'Sensor {i * 4 + j + 1}')
                plot_widget.setLabel('left', 'Value')
                plot_widget.setLabel('bottom', 'Time (s)')
                plot_widget.showGrid(x=True, y=True)
                plot_widget.getAxis('left').setPen('k')
                plot_widget.getAxis('bottom').setPen('k')
                plot_widget.getAxis('left').setTextPen('k')
                plot_widget.getAxis('bottom').setTextPen('k')

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
                plot_grid.addWidget(plot_widget, i, j)

                # Store references
                self.sensor_plots.append({
                    'widget': plot_widget,
                    'curve': curve,
                    'threshold_line': threshold_line,
                    'peaks_scatter': peaks_scatter,
                    'crossings_scatter': crossings_scatter,
                    'data': {'x': [], 'y': []}
                })
>>>>>>> Stashed changes

        sensor_layout.addWidget(QLabel("4x4 Sensor Array"))
        sensor_layout.addLayout(sensor_grid)

        # Add panels to top section
        top_layout.addWidget(fan_panel)
        top_layout.addWidget(sensor_panel)

        # Create middle section with graph views
        middle_section = QWidget()
        middle_layout = QHBoxLayout(middle_section)

        # Graph view panels
        for i in range(2):
            graph_panel = QFrame()
            graph_panel.setFrameStyle(QFrame.Panel | QFrame.Raised)
            graph_layout = QVBoxLayout(graph_panel)

            # Add dropdown for data processing
            data_dropdown = QComboBox()
            data_dropdown.addItems(["Raw Data", "Filtered Data", "Average", "Peak Detection"])

            graph_layout.addWidget(QLabel(f"Live Graph View {i + 1}"))
            graph_layout.addWidget(data_dropdown)
            graph_layout.addWidget(QLabel("Graph Placeholder"))

            middle_layout.addWidget(graph_panel)

        # Create bottom section with log terminal
        log_terminal = QTextEdit()
        log_terminal.setReadOnly(True)
        log_terminal.setPlaceholderText("Log and terminal output will appear here...")

        # Add all sections to main layout
        main_layout.addWidget(top_section)
        main_layout.addWidget(middle_section)
        main_layout.addWidget(log_terminal)

        # Setup timer for sensor simulation
        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.update_sensors)
        self.sensor_timer.start(1000)  # Update every second

<<<<<<< Updated upstream
        self.fan_timer = QTimer()
        self.fan_timer.timeout.connect(self.update_fan_pattern)
        self.fan_timer.start(1000)  # Update every second
=======
        # Setup pattern timer
        self.pattern_timer = QTimer()
        self.pattern_timer.timeout.connect(self.update_fan_pattern)
        self.pattern_timer.start(1000)  # Update every second

        # Initialize sensor data storage
        self.sensor_data = {i: {'times': [], 'values': []} for i in range(16)}
        self.start_time = time.time()
>>>>>>> Stashed changes

    def toggle_fan(self):
        button = self.sender()
        if button.isChecked():
            button.setStyleSheet("background-color: green;")
        else:
            button.setStyleSheet("")

<<<<<<< Updated upstream
    def change_fan_mode(self, mode):
        if mode == "All on":
            for row in self.fan_buttons:
                for button in row:
                    button.setChecked(True)
                    button.setStyleSheet("background-color: green;")
        elif mode == "All off":
            for row in self.fan_buttons:
                for button in row:
                    button.setChecked(False)
                    button.setStyleSheet("")
=======
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
                            self.sensor_plots[i]['data']['x'].append(timestamp)
                            self.sensor_plots[i]['data']['y'].append(value)

                            # Keep only last 100 readings
                            if len(self.sensor_plots[i]['data']['x']) > 100:
                                self.sensor_plots[i]['data']['x'].pop(0)
                                self.sensor_plots[i]['data']['y'].pop(0)

                            # Update plot and detection
                            self.sensor_plots[i]['curve'].setData(
                                self.sensor_plots[i]['data']['x'],
                                self.sensor_plots[i]['data']['y']
                            )

                    # Process detection after updating all plots
                    self.process_current_data()

        except Exception as e:
            self.log_terminal.append(f"Sensor data error: {str(e)}")

    def update_fan_colors(self):
        if not hasattr(self, 'fan_states'):
            self.fan_states = [[0] * 4 for _ in range(4)]
>>>>>>> Stashed changes

    def update_sensors(self):
        for i in range(4):
            for j in range(4):
                # Simulate sensor data
                if random.random() < 0.1:  # 10% chance of no data
                    self.sensor_labels[i][j].setStyleSheet("background-color: red;")
                else:
                    intensity = random.randint(0, 255)
                    self.sensor_labels[i][j].setStyleSheet(
                        f"background-color: rgb({intensity}, {intensity}, 255);"
                    )

<<<<<<< Updated upstream
    def update_fan_pattern(self):
        if self.fan_mode.currentText() == "Random Power":
            for row in self.fan_buttons:
                for button in row:
                    button.setChecked(random.choice([True, False]))
                    button.setStyleSheet("background-color: green;" if button.isChecked() else "")
        elif self.fan_mode.currentText() == "Waves":
            # Implement wave pattern
            pass
=======
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
                            time.sleep(self.pattern_delay)
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
        from scipy.signal import find_peaks

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
>>>>>>> Stashed changes



if __name__ == '__main__':
    app = QApplication(sys.argv)
<<<<<<< Updated upstream
=======

    # Set dark theme
    app.setStyle('Fusion')
>>>>>>> Stashed changes
    window = SensorArrayGUI()
    window.show()
    sys.exit(app.exec_())