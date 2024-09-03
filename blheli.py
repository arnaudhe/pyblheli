
import argparse
import json
from blheli_silabs import BlHeliSilabs
from blheli_atmel import BlHeliAtmel

def parse_key_value_pair(pair):
    """Parses key=value strings into (key, value) tuples."""
    key, value = pair.split("=", 1)
    return key, value

# Create the parser
parser = argparse.ArgumentParser(description="Python BLHeli command-line configurator")

parser.add_argument("port", help="Serial port")
parser.add_argument("--baudrate", type=int, default=115200, help="Serial baudrate")
parser.add_argument("--count", type=int, default=4, help="Number of ESC instances, default is 4")
parser.add_argument("--interface", choices=['atmel', 'silabs'], default='silabs', help="Choose the chip type: 'atmel' or 'silabs'")
parser.add_argument("--verbose", "-v", action="store_true", help="Increase output verbosity")
parser.add_argument("--json", "-j", action="store_true", help="Output data in JSON format to ease integration")

# Create subparsers
subparsers = parser.add_subparsers(dest='command')

# Create get config command
get_config = subparsers.add_parser('get_config', help='Read and display configuration')
get_config.add_argument("--esc", type=int, default=0, help="ESC instance, default is all")

# Create set_config command
set_config = subparsers.add_parser('set_config', help='Write configuraiton parameters')
set_config.add_argument("--esc", type=int, default=0, help="ESC instance, default is all")
set_config.add_argument("--params", nargs="+", action="append", type=parse_key_value_pair, help="Parameters list in the form key=value", required=True)

# Parse the arguments
args = parser.parse_args()

# Instanciate interface and connect to ESC
if args.interface == 'silabs':
    interface = BlHeliSilabs(args.port, args.baudrate, args.count, args.verbose)
else:
    interface = BlHeliAtmel(args.port, args.baudrate, args.count, args.verbose)

try:

    # Connect and test connection
    interface.connect()

    if args.command == 'get_config':

        if args.esc == 0:
            data = interface.read_config_all()
        else:
            data = interface.read_config(args.esc)

    elif args.command == 'set_config':

        # Flatten the list of lists into a dictionary
        params = {key: value for pair in args.params for key, value in pair}
        if args.esc == 0:
            interface.write_config_all(**params)
            data = None
        else:
            interface.write_config(args.esc, **params)
            data = None

    status = 'success'

except Exception as e:

    data = str(e)
    status = 'error'

finally:

    interface.disconnect()


if args.json:
    print(json.dumps({'status': status, 'data': data}))
else:
    print('----------------')
    print('Status:', status)
    print(data)


