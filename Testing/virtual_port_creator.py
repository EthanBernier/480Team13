import subprocess
import sys
import platform


def create_virtual_ports():
    system = platform.system().lower()

    if system in ['linux', 'darwin']:  # Linux or Mac
        try:
            # Check if socat is installed
            subprocess.run(['which', 'socat'], check=True, capture_output=True)

            print("Creating virtual serial port pair...")
            print("Press Ctrl+C to stop")

            # Start socat process
            process = subprocess.Popen(
                ['socat', '-d', '-d', 'pty,raw,echo=0', 'pty,raw,echo=0'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for and parse the port names
            while True:
                line = process.stderr.readline().decode()
                if 'N PTY is' in line:
                    print(line.strip())
                if not line:
                    break

            print("\nVirtual ports created. Keep this window open while testing.")
            process.wait()

        except subprocess.CalledProcessError:
            print("Error: socat is not installed.")
            print("Install it using:")
            if system == 'linux':
                print("  sudo apt-get install socat  # Debian/Ubuntu")
                print("  sudo yum install socat      # RHEL/CentOS")
            else:
                print("  brew install socat          # macOS")

        except KeyboardInterrupt:
            print("\nStopping virtual ports...")
            process.terminate()

    elif system == 'windows':
        print("On Windows, please install COM0COM:")
        print("1. Download from: https://sourceforge.net/projects/com0com/")
        print("2. Install and run the setup utility")
        print("3. Create a new port pair (e.g., COM5 - COM6)")
        print("4. Use these ports in the serial port tester")

    else:
        print(f"Unsupported operating system: {system}")


if __name__ == "__main__":
    create_virtual_ports()