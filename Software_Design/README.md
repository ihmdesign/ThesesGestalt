# Software Design

## Python_Server

Python Lib Requirement:
- [BLEAK](https://bleak.readthedocs.io/en/latest/)

Three programs are available:
1. Python_Test.py

It is used for simple test of the bluetooth control. Users can manually input the vibration parameters in command lines. make sure the CHARACTERISTIC_UUID and CONTROL_UNIT_NAME are the same in control unit's Arduino code. To run the code:
```
Python Python_Test.py -uuid CUSTOM_UUID -name CONTROL_UNIT_NAME

default uuid = 'f22535de-5375-44bd-8ca9-d0ea9ff9e410'
default name = 'QT Py ESP32-S3'
```

2. Python_Play_Command.py

It reads commands from a data file, and plays vibrations accordingly. Data file are written in the following format:
```
{"time": 2.0, "addr": 1, "mode": 1, "duty": 0, "freq": 2}
{"time": 2.03, "addr": 1, "mode": 1, "duty": 1, "freq": 2}
{"time": 2.06, "addr": 1, "mode": 1, "duty": 2, "freq": 2}
```
To run the code:
```
Python Python_Play_Command.py -uuid CUSTOM_UUID -name CONTROL_UNIT_NAME -file FILENNAME

default uuid = 'f22535de-5375-44bd-8ca9-d0ea9ff9e410'
default name = 'QT Py ESP32-S3'
default file = 'command.json'
```

3. Python_Unity_Server.py

It receives vibration commands sent from Unity Engine through socket communication, converts the command format from JSON to bytearray, and sends the commands to the control unit. To run the code:

```
Python Python_Play_Command.py -uuid CUSTOM_UUID -name CONTROL_UNIT_NAME -host HOST_IP -port PORT

default uuid = 'f22535de-5375-44bd-8ca9-d0ea9ff9e410'
default name = 'QT Py ESP32-S3'
default host = '127.0.0.1'
default port = 9051
```
