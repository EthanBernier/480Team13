import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QPushButton, QLabel,
                             QComboBox, QTextEdit, QFrame)
from PyQt5.QtCore import Qt, QTimer
import random


class SensorArrayGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensor Array Interface v.0.01")
        self.setGeometry(100, 100, 1200, 800)

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

        # Fan control dropdown and buttons
        self.fan_mode = QComboBox()
        self.fan_mode.addItems(["Random Power", "Waves", "Custom", "All on", "All off"])
        self.fan_mode.currentTextChanged.connect(self.change_fan_mode)

        fan_layout.addWidget(QLabel("Fan Control Array"))
        fan_layout.addLayout(fan_grid)
        fan_layout.addWidget(QLabel("Programs:"))
        fan_layout.addWidget(self.fan_mode)

        # Sensor Array Panel
        sensor_panel = QFrame()
        sensor_panel.setFrameStyle(QFrame.Panel | QFrame.Raised)
        sensor_layout = QVBoxLayout(sensor_panel)

        # Sensor array (4x4 grid of labels)
        sensor_grid = QGridLayout()
        self.sensor_labels = []
        for i in range(4):
            row = []
            for j in range(4):
                label = QLabel()
                label.setMinimumSize(50, 50)
                label.setStyleSheet("background-color: gray;")
                label.setAlignment(Qt.AlignCenter)
                sensor_grid.addWidget(label, i, j)
                row.append(label)
            self.sensor_labels.append(row)

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

        self.fan_timer = QTimer()
        self.fan_timer.timeout.connect(self.update_fan_pattern)
        self.fan_timer.start(1000)  # Update every second

    def toggle_fan(self):
        button = self.sender()
        if button.isChecked():
            button.setStyleSheet("background-color: green;")
        else:
            button.setStyleSheet("")

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

    def update_fan_pattern(self):
        if self.fan_mode.currentText() == "Random Power":
            for row in self.fan_buttons:
                for button in row:
                    button.setChecked(random.choice([True, False]))
                    button.setStyleSheet("background-color: green;" if button.isChecked() else "")
        elif self.fan_mode.currentText() == "Waves":
            # Implement wave pattern
            pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SensorArrayGUI()
    window.show()
    sys.exit(app.exec_())