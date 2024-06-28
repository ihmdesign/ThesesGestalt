## Electrical Engineering Section ##

The electrical engineering section includes:
### 1. receive_main.c: ###
    Program for the unit driver board that can suport 9-bit asynchronous UART, controlling the actuator, and LED interface.
### 2. buck_receive.c: ###
    Program for the power converter that also supports 9-bit asynchronous UART and modulates the output voltage with 32 bit resolution. It also operates in closed-loop for accurate voltage regulation.
### 3. adc_test.c: ###
    ADC test program for Analog-to-digital-convertion functionality.
### 4. buck_transmit_test: ###
    buck transmit test program.
### 5. closed_loop.c: ###
    buck converter losed-loop operation test program.
### 6. cwg_ccp: ###
    A program that controls the actuator with designated frequencies, waveform, and duty cycle. To generate opposite waveform across the two pogo pins, we utilized conplementary waveform generator feature of the PIC16F18313 MCU.
### 7. transmit_main.c: ###
    A program that tests the functionality of the chain-connection protocol and board-to-board interface.

