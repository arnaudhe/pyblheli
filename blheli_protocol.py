import crcmod
from construct import Byte, Struct, Int8ul, Int16ub, Enum, Const, PrefixedArray, Default

class BLHeliEncodingError(Exception):
    """Exception raised for BLHeli encoding errors.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message
        super().__init__('Encoding error: ' + self.message)

class BLHeliDecodingError(Exception):
    """Exception raised for BLHEli decoding errors.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message
        super().__init__('Decoding error: ' + self.message)

class BLHeliProtocol:
    """
    Helper class to build and parse BLHeli protocol frames
    """

    # Frames start byte
    REQUEST_START_BYTE = 0x2f
    RESPONSE_START_BYTE = 0x2e

    # List of BLHeli commands opcodes
    COMMAND_ENUM = Enum(Byte, interface_test_alive=0x30, 
                              protocol_get_version=0x31,
                              interface_get_name=0x32,
                              interface_get_version=0x33,
                              interface_exit=0x34,
                              device_reset=0x35,
                              device_init_flash=0x37,
                              device_erase_all=0x38,
                              device_page_erase=0x39,
                              device_read=0x3a,
                              device_write=0x3b,
                              device_c2ck_low=0x3c,
                              device_read_eeprom=0x3d,
                              device_write_eeprom=0x3e,
                              interface_set_mode=0x3f)

    # List of response status (ack) code
    ACK_ENUM = Enum(Byte, ok=0x00,
                          invalid_command=0x02,
                          invalid_crc=0x03,
                          verify_error=0x04,
                          invalid_channel=0x08,
                          invalid_param=0x09,
                          general_error=0x0f)

    # Define the command request structure using construct
    REQUEST = Struct(
        "start_byte" / Const(REQUEST_START_BYTE, Byte),     # Start byte, 0x2F for sending
        "command" / COMMAND_ENUM,                           # Command byte
        "address" / Default(Int16ub, 0),                    # 16-bit address
        "payload" / PrefixedArray(Int8ul, Byte),            # Payload depending on command
        "crc" / Int16ub,                                    # CRC16
    )

    # Define the command response structure using construct
    RESPONSE = Struct(
        "start_byte" / Const(RESPONSE_START_BYTE, Byte),    # Start byte, 0x2E for receiving
        "command" / COMMAND_ENUM,                           # Command byte
        "address" / Default(Int16ub, 0),                    # 16-bit address
        "payload" / PrefixedArray(Int8ul, Byte),            # Payload depending on command
        "ack" / ACK_ENUM,                                   # Command status
        "crc" / Int16ub,                                    # CRC16
    )

    # Define payloads
    REQUEST_PAYLOAD = {
        'device_reset': Struct("esc_channel" / Int8ul),
        'device_page_erase': Struct("page_number"/ Int8ul),
        'device_read': Struct("length" / Int8ul),
        'device_write': PrefixedArray(Int8ul, Byte),
        'device_c2ck_low': Struct("esc_channel" / Int8ul),
        'device_read_eeprom': Struct("length" / Int8ul),
        'device_write_eeprom': PrefixedArray(Int8ul, Byte),
        'interface_set_mode': Struct("esc_channel" / Int8ul)
    }

    RESPONSE_PAYLOAD = {
        'device_init_flash': Struct("HiSign" / Byte, "LoSign" / Byte, "BootMsg" / Byte, "mode" / Enum(Byte, SiLabsC2=0, SiLabsBLB=1, AtmelBLB=2, AtmelSK=3))
    }

    # Create XMODEM CRC16 function
    CRC16_XMODEM = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)

    @staticmethod
    def build(command, address=0, payload=[0]):
        """Build and encode a command frame"""
        try:
            # Encode the frame a first time with dummy CRC16
            frame = BLHeliProtocol.REQUEST.build(dict(command=command, address=address, payload=payload, crc=0))
            # Compute CRC16
            crc = BLHeliProtocol.CRC16_XMODEM(frame[:-2])
            # Reencode frame with right CRC16
            frame = BLHeliProtocol.REQUEST.build(dict(command=command, address=address, payload=payload, crc=crc))
        except Exception as e:
            raise BLHeliEncodingError(str(e))
        return frame
    
    @staticmethod
    def parse(frame):
        """Parse and decode a received frame"""
        # Check parameter
        if not len(frame):
            raise BLHeliDecodingError(f"Null length frame")
        # Parse frame
        try:
            parsed = BLHeliProtocol.RESPONSE.parse(frame)
        except Exception as e:
            raise BLHeliDecodingError(str(e))
        # Check start byte
        if parsed.start_byte != BLHeliProtocol.RESPONSE_START_BYTE:
            raise BLHeliDecodingError(f"Invalid start byte ({parsed.start_byte})")
        # Check crc16
        if parsed.crc != BLHeliProtocol.CRC16_XMODEM(frame[:-2]):
            raise BLHeliDecodingError(f"Invalid crc ({frame[-2:].hex()})")
        return parsed

    @staticmethod
    def parse_payload(frame):
        """Parse payload, based on command identifier"""
        # Extract raw payload in bytes
        raw_payload = bytes(frame.payload)
        # Check if the frame is a request or a response, to retreive payload structure
        payload_structs = BLHeliProtocol.REQUEST_PAYLOAD if frame.start_byte == BLHeliProtocol.REQUEST_START_BYTE else BLHeliProtocol.RESPONSE_PAYLOAD
        # If payload struct is known, parse it. Otherwise return raw payload
        if frame.command in payload_structs:
            try:
                return payload_structs[frame.command].parse(raw_payload)
            except Exception as e:
                raise BLHeliDecodingError('Failed to parse payload ' + str(e))
        else:
            return raw_payload

if __name__ == '__main__':

    print('Test - Parse - command')
    parsed = BLHeliProtocol.parse(bytes.fromhex("2E3400000100004263"))
    assert(str(parsed.command) == 'interface_exit')

    print('Test - Parse - crc verification')
    try:
        BLHeliProtocol.parse(bytes.fromhex("2E3400000100004264"))
        # We must raise an exception because CRC is wrong
        assert(False)
    except BLHeliDecodingError:
        pass

    print('Test - Parse - payload')
    parsed = BLHeliProtocol.parse(bytes.fromhex("2E37000004F330AA0100F7F0"))
    assert(str(BLHeliProtocol.parse_payload(parsed).mode) == 'SiLabsBLB')

    print('Test - Build')
    built = BLHeliProtocol.build('device_erase_all')
    assert(built.hex() == "2f3800000100cdf9")

    print('Test - Build - params')
    built = BLHeliProtocol.build('device_read', address=0xaabb, payload=[15])
    assert(built.hex() == "2f3aaabb010ff446")
