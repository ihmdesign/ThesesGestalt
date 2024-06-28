from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication
from bleak import BleakScanner, BleakClient
import time
import asyncio
import sys
import json

class BluetoothHandler(QObject):
    MOTOR_UUID = 'f22535de-5375-44bd-8ca9-d0ea9ff9e410'

    async def main(self):
        devices = await BleakScanner.discover()
        for d in devices:
            # print('device name = ', d.name)
            if d.name != None:
                if d.name == 'FEATHER_ESP32':
                    print('feather device found!!!')
                    self.client = BleakClient(d.address)  # Pass the event loop
                    await self.client.connect()
                    print('connected')
                    print('mtu_size = ', self.client.mtu_size)
                    val = await self.client.read_gatt_char(self.MOTOR_UUID)
                    print('Motor read = ', val)

    def __init__(self, loop) -> None:
        super().__init__()
        self.client = None
        self.loop = loop  # Get the event loop

    def __del__(self):
        if self.client is not None:
            self.loop.run_until_complete(self.client.disconnect())  # Use the event loop to disconnect

    async def bluetooth_handler_callback(self, command): # send command in as string, json separated by \n
        print(f"Received Bluetooth command: {command}")
        commands = command.split('\n')
        output_string = ''
        command_idx = 0
        time_offset = time.perf_counter() # record the starting time
        while command_idx < len(commands):
            # collect commands that are at the same time and form the output
            output_string = commands[command_idx]
            command_parsed = json.loads(commands[command_idx])
            ts = float(command_parsed['time'])
            command_idx += 1
            command_count = 1 # max allowed in one command is 7
            while True:
                if command_count == 7:
                    break
                if command_idx < len(commands):
                    command_parsed = json.loads(commands[command_idx])
                    if (ts+1e-6) > float(command_parsed['time']): # basically two commands are at the same time
                        output_string += '\n' + commands[command_idx]
                        command_idx += 1
                        command_count += 1
                    else:
                        break
                else:
                    break
            # wait for the send time
            print('command time = ', ts)
            start = time.perf_counter()
            # await asyncio.sleep(ts-current_time)
            while (time.perf_counter()-time_offset) < ts:
                pass
            actual_sleep_duration = time.perf_counter() - start
            print(f"{start}, Actual sleep duration: {actual_sleep_duration} seconds")
            print('commands = \n', output_string)
            output = bytearray(output_string, 'utf-8')
            # print('command len = ', len(output))
            print(time.perf_counter())
            await self.client.write_gatt_char(self.MOTOR_UUID,  output)
            print(time.perf_counter())

# Worker thread for Bluetooth handling
class BluetoothCommandThread(QThread):

    def __init__(self, loop):
        super().__init__()
        self.loop = loop

    def run(self):
        self.handler = BluetoothHandler(self.loop)
        self.handler.loop.run_until_complete(self.handler.main())

    def bluetooth_callback(self, command):
        print(f"Received Bluetooth Thread: {command}")
        self.handler.loop.run_until_complete(self.handler.bluetooth_handler_callback(command))

# Run the main function
if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = asyncio.get_event_loop()
    bluetooth_thread = BluetoothCommandThread(loop)
    bluetooth_thread.start()
    sys.exit(app.exec_())