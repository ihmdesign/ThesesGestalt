# **VibraForge: A Scalable Prototyping Toolkit For Creating Spatialized Vibrotactile Feedback Systems** #

This repository shares the open-source design files of the VibraForge toolkit, including mechanical design, electrical design, software design, and GUI editor. 

- Electrical Design
- GUI Editor
- Mechanical Design
- Software Design

If you are interested in using the toolkit and would like to get a development kit from us, please fill out [this Google Form](https://forms.gle/6aN7M9MWAf4sLqWE6)

## Quickstart Guidelines

If you already have the hardware dev kit shipped by the authors, it should contain a [quickstart guide](quickstart_guide.pdf) that you can easily follow.

Otherwise, you can follow step 1 & 2 to make the hardware yourself.

1. The `Electrical Design` folder has detailed descriptions of how to use the PCB design files to print the boards, and to program the boards with Arduino / MPLab X IDE.

2. The `Mechanical Design` folder contains all the CAD design files to print the parts.

3. Once all the hardware is setup, an easy place to start is to run the `Software_Design/Python_Server/Python_Test.py` program. It is used for simple test of the bluetooth control. You can manually input the vibration parameters in command lines. make sure the CHARACTERISTIC_UUID and CONTROL_UNIT_NAME are the same in control unit's Arduino code. To run the code:
```
Python Python_Test.py -uuid CUSTOM_UUID -name CONTROL_UNIT_NAME

default uuid = 'f22535de-5375-44bd-8ca9-d0ea9ff9e410'
default name = 'QT Py ESP32-S3'
```

4. If everything works well with `Python_Test.py`, then you can proceed to integrate the toolkit into your system! If you want to experiment with different vibration waveforms, you can use the `GUI_Editor` to try different waveforms, such as Sine, PWM, Triangle and Saw, etc. If you want to integrate the toolkit into Unity Engine developments, Use the `Software_design/Unity_Engine_API`. 

For detailed descriptions of each step, please refer to the `readme` files in the subfolders.

## Some Notes for Debugging

### Control Unit

Regarding the control unit, **the order of the four chain connectors** are shown in the figure. Also note that the USB port should be facing left. Putting it in the wrong direction may result in shorting the ESP32 MCU. 

If the MCU is not working for some unknown reasons, it might be a good idea to factory reset it following [this link](https://learn.adafruit.com/adafruit-qt-py-esp32-s3/factory-reset).

<img src="Figures/control_unit.png" alt="Control Unit Notes" width="800">

### Vibration Unit

The unit address on each chain **starts from 0**. Maximum sixteen units can be connected to each chain. Therefore, the units on the first chain have address 0,1,2,...,15; The units on the second chain have address 16,17,...,31. When the programming pins are on the top, the input is on the left side, and the output is on the right side. Do not reverse the order, or the unit driver board might damage due to shortage.

Each vibration unit driver PCB has **two LEDs**. When the first LED lights up, it indicates that the board is correctly powered, when the second LED lights up, it indicates that it receives "Start" commands and should be vibrating. These two LEDs can be useful for checking MCU status during debugging.

<img src="Figures/vibration_unit.png" alt="Control Unit Notes" width="800">

## Bug Report

If you identify any bug while using the toolkit, feel free to submit a new issue! The authors would try to resolve them ASAP :D

Have fun with the toolkit!
