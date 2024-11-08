import serial
import time
import math
import random
from serial.tools.list_ports_common import ListPortInfo
from typing import List


class MockSerial:
    """Mock Serial port for testing"""

    def __init__(self, port='COM1', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.is_open = True
        self.in_waiting = True
        self._data_generator = self._generate_sensor_data()
        self.start_time = time.time()

        # Different frequencies and phases for each sensor
        self.sensor_configs = [
            {'freq': 0.2, 'phase': 0, 'amplitude': 400},  # Sensor 1: Slow oscillation
            {'freq': 0.5, 'phase': math.pi / 4, 'amplitude': 350},  # Sensor 2: Medium oscillation
            {'freq': 1.0, 'phase': math.pi / 2, 'amplitude': 300},  # Sensor 3: Fast oscillation
            {'freq': 0.1, 'phase': math.pi / 6, 'amplitude': 450},  # Sensor 4: Very slow oscillation
            {'freq': 0.7, 'phase': math.pi / 3, 'amplitude': 250},  # Sensor 5: Custom oscillation
            {'freq': 0.3, 'phase': math.pi, 'amplitude': 380},  # Sensor 6: Another pattern
            {'freq': 0.8, 'phase': 3 * math.pi / 4, 'amplitude': 320},  # Sensor 7: Different pattern
            {'freq': 1.2, 'phase': math.pi / 8, 'amplitude': 280},  # Sensor 8: Faster pattern
            {'freq': 0.4, 'phase': 5 * math.pi / 6, 'amplitude': 420},  # Sensor 9: Medium-slow pattern
            {'freq': 0.6, 'phase': 7 * math.pi / 8, 'amplitude': 360}  # Sensor 10: Medium pattern
        ]

    def close(self):
        self.is_open = False

    def readline(self) -> bytes:
        """Simulate sensor data in the format: START,timestamp,S1:val,S2:val,...,S10:val,END"""
        try:
            return next(self._data_generator)
        except StopIteration:
            self._data_generator = self._generate_sensor_data()
            return next(self._data_generator)

    def write(self, data: bytes) -> int:
        """Mock write method"""
        return len(data)

    def _generate_burst_noise(self, time_val, sensor_idx):
        """Generate occasional burst noise"""
        if random.random() < 0.02:  # 2% chance of burst noise
            return random.uniform(100, 200)
        return 0

    def _generate_drift(self, time_val, sensor_idx):
        """Generate slow drift in the baseline"""
        return 50 * math.sin(0.05 * time_val + sensor_idx)

    def _generate_sensor_value(self, elapsed_time, sensor_idx):
        """Generate a single sensor value with multiple components"""
        config = self.sensor_configs[sensor_idx]

        # Base oscillation
        base = 512 + config['amplitude'] * math.sin(
            2 * math.pi * config['freq'] * elapsed_time + config['phase']
        )

        # Add drift
        drift = self._generate_drift(elapsed_time, sensor_idx)

        # Add random noise
        noise = random.gauss(0, 10)

        # Add burst noise
        burst = self._generate_burst_noise(elapsed_time, sensor_idx)

        # Combine all components and ensure value stays within ADC range (0-1023)
        value = base + drift + noise + burst
        return max(0, min(1023, value))

    def _generate_sensor_data(self):
        """Generator for simulated sensor data"""
        while True:
            elapsed_time = time.time() - self.start_time
            timestamp = int(elapsed_time * 1000)  # Current time in milliseconds

            # Generate values for all sensors
            sensor_values = []
            for i in range(10):
                value = self._generate_sensor_value(elapsed_time, i)
                sensor_values.append(f"S{i + 1}:{int(value)}")

            # Format the complete line
            line = f"START,{timestamp},{','.join(sensor_values)},END\n"
            yield line.encode()

            # Add a small delay to simulate real sensor reading intervals
            time.sleep(0.05)  # 50ms delay between readings


class MockListPorts:
    """Mock list_ports for testing"""

    @staticmethod
    def comports() -> List[ListPortInfo]:
        mock_port = ListPortInfo('MOCK1')
        mock_port.device = 'MOCK1'
        mock_port.description = 'Mock Serial Port'
        return [mock_port]


# Monkey-patch serial.Serial and list_ports
serial.Serial = MockSerial
serial.tools.list_ports = MockListPorts

if __name__ == "__main__":
    # Test the mock serial port
    mock_serial = MockSerial()
    print("Starting sensor simulation... Press Ctrl+C to stop")
    try:
        while True:
            print(mock_serial.readline().decode(), end='')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nSimulation stopped")