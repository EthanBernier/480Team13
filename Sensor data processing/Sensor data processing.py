import serial
import time
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import threading

# Configure these variables!!!!
SERIAL_PORT = '/dev/ttyACM0'  # Change this to match your Arduino's serial port
BAUD_RATE = 115200
DATA_COLLECTION_TIME = 60  # How long the program runs in seconds

# Global variables
data = []
data_lock = threading.Lock()


def read_serial_data():
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        start_time = time.time()
        while time.time() - start_time < DATA_COLLECTION_TIME:
            line = ser.readline().decode('utf-8').strip()
            if line.startswith('START') and line.endswith('END'):
                parts = line.split(',')
                timestamp = int(parts[1])
                sensor_data = parts[2:-1]
                with data_lock:
                    for sensor in sensor_data:
                        name, value = sensor.split(':')
                        data.append({'Timestamp': timestamp, 'Sensor': name, 'Value': int(value)})


def process_data_and_generate_report():
    with data_lock:
        df = pd.DataFrame(data)

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')

    with open('sensor_data_report.md', 'w') as md_file:
        md_file.write("# Sensor Data Report\n\n")
        md_file.write(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for sensor in df['Sensor'].unique():
            sensor_data = df[df['Sensor'] == sensor]

            plt.figure(figsize=(10, 5))
            plt.plot(sensor_data['Timestamp'], sensor_data['Value'])
            plt.title(f'{sensor} Data')
            plt.xlabel('Time')
            plt.ylabel('Sensor Value')
            plt.xticks(rotation=45)
            plt.tight_layout()

            plot_filename = f'{sensor}_plot.png'
            plt.savefig(plot_filename)
            plt.close()

            md_file.write(f"## {sensor} Data\n\n")
            md_file.write(f"![{sensor} Plot]({plot_filename})\n\n")
            md_file.write("### Statistics\n\n")
            md_file.write(f"- Mean: {sensor_data['Value'].mean():.2f}\n")
            md_file.write(f"- Median: {sensor_data['Value'].median():.2f}\n")
            md_file.write(f"- Min: {sensor_data['Value'].min()}\n")
            md_file.write(f"- Max: {sensor_data['Value'].max()}\n")
            md_file.write(f"- Standard Deviation: {sensor_data['Value'].std():.2f}\n\n")

    print("Data processing and report generation complete.")


if __name__ == "__main__":
    print(f"Starting data collection for {DATA_COLLECTION_TIME} seconds...")
    read_serial_data()
    print("Data collection complete. Processing data and generating report...")
    process_data_and_generate_report()