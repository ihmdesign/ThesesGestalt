import asyncio
from bleak import BleakScanner, BleakClient
import json
import time

MOTOR_UUID = 'f22535de-5375-44bd-8ca9-d0ea9ff9e410'

file_commands = 'commands/commands_pressure_test_20230827.json'

'''
commands_side_center.json
commands_linear_stroke.json
commands_vertical_stroke.json
commands_cross_pattern.json
'''

# async def setMotor(client):
#     while True:
#         motor_addr = int(input('what is the next motor you want to control?'))
#         start_or_stop = int(input('1 for start and 0 for stop?'))
#         # duty = int(input('0-3 for duty?'))
#         command = {
#             'addr':motor_addr,
#             'mode':start_or_stop,
#             'duty':3, # default
#             'freq':2, # default
#             'wave':1, # default
#         }
#         output = bytearray(json.dumps(command), 'utf-8')
#         await client.write_gatt_char(MOTOR_UUID,  output)

async def sendCommands(client):
    with open(file_commands) as f:
        commands = f.readlines()
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
                        output_string += commands[command_idx]
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
            # print('commands = \n', output_string)
            output = bytearray(output_string, 'utf-8')
            # print('command len = ', len(output))
            print(time.perf_counter())
            await client.write_gatt_char(MOTOR_UUID,  output)
            print(time.perf_counter())
            

async def main():
    devices = await BleakScanner.discover()
    for d in devices:
        print('device name = ', d.name)
        if d.name != None:
            if d.name == 'FEATHER_ESP32':
                print('feather device found!!!')
                async with BleakClient(d.address) as client:
                    print(f'BLE connected to {d.address}')
                    print('mtu_size = ', client.mtu_size)
                    val = await client.read_gatt_char(MOTOR_UUID)
                    print('Motor read = ', val)
                    await sendCommands(client)

asyncio.run(main())