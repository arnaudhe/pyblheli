from blheli_4way import BLHeli4WayInterface
from blheli_log import log

class BlHeliAtmel(BLHeli4WayInterface):
    """
    Manipulate a BLHeli Silabs ESC configuration over a 4-way interface
    !!! WARNING !!! This class is not fully implemented yet, and thus not working
    """

    def __init__(self, port, baudrate=115200, count=4, verbose=False):
        super().__init__(port, baudrate, count, verbose)

    def connect(self):
        """Connect serial port and test communication"""
        # Open serial port
        super().connect()
        self.flush_input()
        # Test connection
        self.test_alive()
        # Interface name
        log('Interface name:', self.get_name())

    def read_config(self, esc):
        """Read config from device memory. Return a tuple containing (device_info, common_config, esc_config)"""
        raise Exception("Not implemented")

    def read_config_all(self):
        """Read config from device memory. Return a tuple containing (device_info, configs)"""
        raise Exception("Not implemented")

    def write_config(self, **params):
        """Read parameters into device config memory"""
        raise Exception("Not implemented")
