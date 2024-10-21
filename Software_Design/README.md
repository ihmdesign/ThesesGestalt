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
Python Python_Unity_Server.py -uuid CUSTOM_UUID -name CONTROL_UNIT_NAME -host HOST_IP -port PORT

default uuid = 'f22535de-5375-44bd-8ca9-d0ea9ff9e410'
default name = 'QT Py ESP32-S3'
default host = '127.0.0.1'
default port = 9051
```

## Unity_Engine_API

We also provide a Unity Engine API so that designers can directly make function calls to control vibrations. To get started, you can run the VibraForge_Plugin Unity project and see how the function calls are used to trigger vibrations when a ball collides with a wall. To integrate it into your own project,

1. Import `VibraForge_Plugin.unitypackage` as a custom package into an existing project.
2. Use the `VibraForgeSender` prefab to create a new gameobject, and configure the server IP address and port if needed. 
3. When Unity Engine events are triggered (e.g., OnTriggerEnter, OnTriggerExit, etc), call `VibraForge.SendCommand(addr, mode, duty, freq)` to send vibration commands.
4. Note: the Python_Unity_Server.py program is used to receive vibration commands through socket communication with Unity Engine APIs. it should be run before running the Unity program.