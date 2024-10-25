import serial
import time
import random
import sys
from serial.tools import list_ports


class VirtualSensorDevice:
    def __init__(self, port):
        self.serial_port = serial.Serial(port, 115200, timeout=1)
        print(f"Virtual sensor device started on {port}")

    def run(self):
        while True:
            try:
                # Generate sample sensor data
                timestamp = int(time.time() * 1000)
                packet = f"START,{timestamp},"

                # Generate readings for 16 sensors
                for s in range(16):
                    for board in range(2):
                        value = random.randint(0, 1023)
                        packet += f"S{s + 1}A{board}:{value},"

                packet += "END\n"

                # Send packet
                self.serial_port.write(packet.encode())
                print(f"Sent: {packet.strip()}")

                # Wait before next sample
                time.sleep(0.2)

            except KeyboardInterrupt:
                print("\nStopping virtual device...")
                self.serial_port.close()
                break
            except Exception as e:
                print(f"Error: {str(e)}")
                break


def list_available_ports():
    return [port.device for port in list_ports.comports()]


if __name__ == "__main__":
    ports = list_available_ports()
    print("Available ports:")
    for i, port in enumerate(ports):
        print(f"{i}: {port}")

    if not ports:
        print("No ports available!")
        sys.exit(1)

    choice = int(input("Select port number: "))
    if 0 <= choice < len(ports):
        device = VirtualSensorDevice(ports[choice])
        device.run()
    else:
        print("Invalid port selection!")