import serial
import time

from blheli_log import log
from blheli_protocol import BLHeliProtocol as protocol

class BLHeli4WayInterface:
    """
    BLHeli 4-way configuration interface abstraction
    This interface relies on a serial link, which can be achieved with
     * native ESC serial port
     * Flight Controller with passthrough support (ArduPilot, Betaflight, Cleanflight)
     * 4-way Arduino interface
    """

    def __init__(self, port, baudrate=115200, count=4, verbose=False):
        self.verbose = verbose
        self.count = count
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None

    def connect(self):
        """Connect serial port"""
        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=1)
            log(f"Connected to {self.port} at {self.baudrate} baud.")
            time.sleep(0.5)
            self.flush_input()
        except serial.SerialException:
            raise Exception(f"Failed to connect to {self.port}")

    def disconnect(self):
        """Disconnect serial port"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            log("Disconnected.")
    
    def flush_input(self):
        """Discard all pending serial data"""
        self.serial_connection.flush()

    def send_command(self, command, address=0, payload=[0]):
        """Send a command to the ESC."""
        frame = protocol.build(command, address, payload)
        self.serial_connection.write(frame)
        if self.verbose:
            log("->", frame.hex())
        time.sleep(0.1)  # Short delay for ESC to process

    def read_response(self, expected_length=64):
        """Read and decode response from the ESC."""
        response = self.serial_connection.read(expected_length)
        if self.verbose:
            log("<-", response.hex())
        return protocol.parse(response)
    
    def init_flash(self, esc):
        """Init device flash and return interface type ("silabs" or "atmel")"""
        self.send_command('device_init_flash', payload=[esc])
        payload = protocol.parse_payload(self.read_response())
        if payload.mode in ('SiLabsC2', 'SiLabsBLB'):
            return 'silabs'
        else:
            return 'atmel'
        
    def erase_page(self, page):
        """!!! Erase one page in device memory"""
        self.send_command('device_page_erase', payload=[page])
        self.read_response()

    def write_memory(self, address, data):
        """!!! Write data to device memory"""
        self.send_command('device_write', address, data)
        return self.read_response()

    def read_memory(self, address, length):
        """Read data from device memory."""
        self.send_command('device_read', address, [length])
        return bytes(self.read_response(length + 8).payload)

    def reset_esc(self, esc):
        """Reset the ESC."""
        self.send_command(command='device_reset', payload=[esc])
        self.read_response()
        time.sleep(1.0)

    def get_name(self):
        """Read and return interface name"""
        self.send_command(command='interface_get_name')
        return bytes(self.read_response()['payload'][1:]).decode('utf-8')
    
    def test_alive(self):
        """Identify ESC (generate a startup tone) and assert that communication is working"""
        self.send_command('interface_test_alive')
        self.read_response()

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description="BLHeli ESC 4-way interface testing")
    parser.add_argument("port", help="Serial port")
    args = parser.parse_args()

    interface = BLHeli4WayInterface(args.port, 115200, True)

    interface.connect()
    interface.test_alive()
    interface.disconnect()