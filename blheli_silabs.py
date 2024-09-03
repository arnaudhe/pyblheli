from blheli_4way import BLHeli4WayInterface
from construct import Byte, Struct, Int16ub, Enum, Padding, Flag, PaddedString
from blheli_log import log

class BlHeliSilabs(BLHeli4WayInterface):
    """
    Manipulate a BLHeli Silabs ESC configuration over a 4-way interface
    """

    CONFIG_ADDRESS = 0x1A00
    PAGE_SIZE      = 0x200

    EEPROM_LAYOUT = Struct(                                                                                                                         # TOTAL SIZE : 0x70
        "main_revision" /              Byte,                                                                                                        # offset: 0x00, size: 1
        "sub_revision" /               Byte,                                                                                                        # offset: 0x01, size: 1
        "layout_revision" /            Byte,                                                                                                        # offset: 0x02, size: 1
        Padding(6, pattern=b'\xff'),                                                                                                                # offset: 0x03, size: 6
        "startup_power" /              Enum(Byte, **{'0.031': 1, '0.047': 2, '0.063': 3, '0.094': 4, '0.125': 5, '0.188': 6, '0.25': 7,             # offset: 0x09, size: 1
                                                     '0.38': 8, '0.50': 9, '0.75': 10, '1.00': 11, '1.25': 12, '1.50': 13}),
        Padding(1, pattern=b'\xff'),                                                                                                                # offset: 0x0A, size: 1
        "motor_direction" /            Enum(Byte, normal=1, reversed=2, bidir=3, bidir_reversed=4),                                                 # offset: 0x0B, size: 1
        Padding(1, pattern=b'\xff'),                                                                                                                # offset: 0x0C, size: 1
        "mode" /                       Enum(Int16ub, main=0xA55A, tail=0x5AA5, multi=0x55AA),                                                       # offset: 0x0D, size: 2
        "programming_by_tx" /          Flag,                                                                                                        # offset: 0x0F, size: 1
        Padding(5, pattern=b'\xff'),                                                                                                                # offset: 0x10, size: 5
        "commutation_timing" /         Enum(Byte, low=1, medium_low=2, medium=3, medium_high=4, high=5),                                            # offset: 0x15, size: 1
        Padding(3, pattern=b'\xff'),                                                                                                                # offset: 0x16, size: 3
        "ppm_min_throttle" /           Byte,                                                                                                        # offset: 0x19, size: 1
        "ppm_max_throttle" /           Byte,                                                                                                        # offset: 0x1A, size: 1
        "beep_strength" /              Byte,                                                                                                        # offset: 0x1B, size: 1
        "beacon_strength" /            Byte,                                                                                                        # offset: 0x1C, size: 1
        "beacon_delay" /               Enum(Byte, **{'1_min': 1, '2_min': 2, '5_min': 3, '10_min': 4, 'infinite': 5}),                              # offset: 0x1D, size: 1
        Padding(1, pattern=b'\xff'),                                                                                                                # offset: 0x1E, size: 1
        "demag_compensation" /         Enum(Byte, off=1, low=2, high=3),                                                                            # offset: 0x1F, size: 1
        Padding(1, pattern=b'\xff'),                                                                                                                # offset: 0x20, size: 1
        "ppm_center_throttle" /        Byte,                                                                                                        # offset: 0x21, size: 1
        Padding(1, pattern=b'\xff'),                                                                                                                # offset: 0x22, size: 1
        "temperature_protection" /     Enum(Byte, **{'disabled': 0, '80°': 1, '90°': 2, '100°': 3, '110°': 4, '120°': 5, '130°': 6, '140°': 7}),    # offset: 0x23, size: 1
        "low_rpm_power_protection" /   Flag,                                                                                                        # offset: 0x24, size: 1
        Padding(2, pattern=b'\xff'),                                                                                                                # offset: 0x25, size: 2
        "brake_on_stop" /              Flag,                                                                                                        # offset: 0x27, size: 1
        "led_control" /                Flag,                                                                                                        # offset: 0x28, size: 1
        Padding(23, pattern=b'\xff'),                                                                                                               # offset: 0x29, size: 23
        "layout" /                     PaddedString(16, "utf8"),                                                                                    # offset: 0x40, size: 16
        "mcu" /                        PaddedString(16, "utf8"),                                                                                    # offset: 0x50, size: 16
        "name" /                       PaddedString(16, "utf8"),                                                                                    # offset: 0x60, size: 16
    )

    DEVICE_INFO_FIELDS = ['main_revision', 'sub_revision', 'mode', 'layout', 'mcu', 'name']

    COMMON_CONFIG_FIELDS = ['programming_by_tx', 'commutation_timing', 'beep_strength', 'beacon_strength', 'beacon_delay', 'demag_compensation', 
                            'temperature_protection', 'low_rpm_power_protection', 'brake_on_stop', 'led_control', 'startup_power']

    ESC_CONFIG_FIELDS = ['motor_direction', 'ppm_min_throttle', 'ppm_max_throttle', 'ppm_center_throttle']

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

    def probe_esc(self, esc):
        """Probe ESC instance and check interface type"""
        # Check parameter
        assert(esc >= 0 and esc < self.count)
        # Probe ESC and reset to deinit flash
        log('Probing ESC #', esc + 1)
        interface_type = self.init_flash(esc)
        self.reset_esc()
        # Check interface type
        if interface_type != 'silabs':
            raise Exception(f'Invalid ESC #{esc + 1} type {interface_type}')

    def read_config(self, esc):
        """Read config from device memory. Return a tuple containing (device_info, common_config, esc_config)"""
        # Check parameter
        assert(esc >= 0 and esc < self.count)
        # Read EEPROM content from memory
        self.init_flash(esc)
        eeprom = self.EEPROM_LAYOUT.parse(self.read_memory(BlHeliSilabs.CONFIG_ADDRESS, self.EEPROM_LAYOUT.sizeof()))
        # Reset ESC to deinit flash and load config
        self.reset_esc(esc)
        # Extract device info, common and specific config from layout
        device_info = {field: str(eeprom[field]).strip() for field in self.DEVICE_INFO_FIELDS}
        common_config = {field: eeprom[field] for field in self.COMMON_CONFIG_FIELDS}
        esc_config = {field: eeprom[field] for field in self.ESC_CONFIG_FIELDS}
        return (device_info, common_config, esc_config)

    def read_config_all(self):
        """Read config from device memory. Return a tuple containing (device_info, configs)"""
        escs = []
        for esc in range(self.count):
            esc_info, esc_common_config, esc_config = self.read_config(esc)
            escs.append(dict(info=esc_info, config=esc_config))
            if esc == 0:
                common_config = esc_common_config
            else:
                if common_config != esc_common_config:
                    log(f"Warning : Common config mismatch for ESC #{esc + 1}")
        return (common_config, escs)

    def write_config(self, esc, **params):
        """Read parameters into device config memory"""
        # Check parameter
        assert(esc >= 0 and esc < self.count)
        # Read EEPROM content from memory
        self.init_flash(esc)
        eeprom = self.EEPROM_LAYOUT.parse(self.read_memory(BlHeliSilabs.CONFIG_ADDRESS, self.EEPROM_LAYOUT.sizeof()))
        # Patch EEPROM contents with updated parameters
        for key, value in params.items():
            if key in BlHeliSilabs.COMMON_CONFIG_FIELDS or key in BlHeliSilabs.ESC_CONFIG_FIELDS:
                eeprom[key] = value
            else:
                log('Invalid parameter', key)
        # Write back config in memory
        self.erase_page(int(BlHeliSilabs.CONFIG_ADDRESS / BlHeliSilabs.PAGE_SIZE))
        self.write_memory(BlHeliSilabs.CONFIG_ADDRESS, self.EEPROM_LAYOUT.build(eeprom))
        # Reset ESC to deinit flash and load config
        self.reset_esc(esc)

    def write_config_all(self, **params):
        """Read parameters into device config memory"""
        for esc in range(self.count):
            log(f'ESC #{esc + 1}')
            self.write_config(esc, **params)

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description="Silabs BLHeli testing")
    parser.add_argument("port", help="Serial port")
    args = parser.parse_args()

    interface = BlHeliSilabs(args.port, 115200, 1, True)

    interface.connect()
    print(interface.read_config_all())
    interface.disconnect()
