# pyblheli
Python command-line configurator for BLHeli ESCs

## Disclaimer

This software is provided as is, use it at your own risk. **ALWAYS REMOVE THE PROPELLERS**.

## Features

* 4-way interface (native, FC passthrough or Arduino interface)
* Reading and changing settings for **SiLabs ESCs with last BLHeli_S version**

## Not supported (yet)

* Atmel ESCs
* Firmware flashing
* BLHeli32

## Installing

It is recommanded to work in a python virtual environment, managed by `venv`, `virtualenv`, `pew` and ay other env manager.

Then install dependencies

```
pip install -r requirements.txt
```

## Usage

Command-line entry point is `blheli.py`

Then, invoke command line with

```
python blheli.py
```

```
positional arguments:
  port                  Serial port
  command {get_config,set_config}
    get_config          Read and display configuration
    set_config          Write configuraiton parameters

options:
  -h, --help            show this help message and exit
  --baudrate BAUDRATE   Serial baudrate
  --count COUNT         Number of ESC instances, default is 4
  --interface {atmel,silabs}
                        Choose the chip type: 'atmel' or 'silabs'
  --verbose, -v         Increase output verbosity
  --json, -j            Output data in JSON format to ease integration
```

### Get config

```
usage: blheli.py port get_config [-h] [--esc ESC]

options:
  -h, --help  show this help message and exit
  --esc ESC   ESC instance, default is all
```

### Set config

```
usage: blheli.py port set_config [-h] [--esc ESC] --params PARAMS [PARAMS ...]

options:
  -h, --help            show this help message and exit
  --esc ESC             ESC instance, default is all
  --params PARAMS [PARAMS ...]
                        Parameters list in the form key=value
```
