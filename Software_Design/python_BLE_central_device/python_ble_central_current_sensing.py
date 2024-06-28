import asyncio
from bleak import BleakScanner, BleakClient
import json

CURRENTSENSING_UUID = "640b8bf5-3c88-44f6-95e0-f5813b390d78"
MOTOR_UUID = 'f22535de-5375-44bd-8ca9-d0ea9ff9e410'
MOTOR_NUM = 8

current_zero = 0
buck_addr = 210

async def setMotor(client):
    global current_zero
    # data format for the power converter
    command = {
        'addr':buck_addr, 
        'mode':1,
        'duty':1, # default
        'freq':3, # default
        'wave':1, # default
    }
    # turn on the converter
    output = bytearray(json.dumps(command), 'utf-8')
    print(output)
    await client.write_gatt_char(MOTOR_UUID,  output)
    # start to test individual motors
    command = {
        'addr':0,
        'mode':1,
        'duty':15, # default
        'freq':2, # default
        'wave':0, # default
    }
    for i in range(1, MOTOR_NUM+1):
        command['addr'] = buck_addr+i # for testing the odd number motors
        command['mode'] = 1 # start
        output = bytearray(json.dumps(command), 'utf-8')
        # print(output)
        await client.write_gatt_char(MOTOR_UUID,  output)
        await asyncio.sleep(0.2)

        # val = await client.read_gatt_char(CURRENTSENSING_UUID)
        # res = int(val)
        # if res >= (current_zero + 30):
        #     print(f'Motor # {i} is ON, current = {res}')
        # else:
        #     print(f'Motor # {i} is OFF, current = {res}')
        print(f'Motor # {i}')
        
        command['mode'] = 0 # stop
        output = bytearray(json.dumps(command), 'utf-8')
        # print(output)
        await client.write_gatt_char(MOTOR_UUID,  output)
        await asyncio.sleep(0.2)
    
    command = {
        'addr':buck_addr,
        'mode':0,
        'duty':3, # default
        'freq':3, # default
        'wave':1, # default
    }
    # turn on the converter
    output = bytearray(json.dumps(command), 'utf-8')
    print(output)
    await client.write_gatt_char(MOTOR_UUID,  output)


async def main():
    global current_zero
    devices = await BleakScanner.discover()
    for d in devices:
        print('device name = ', d.name)
        if d.name != None:
            if d.name == 'FEATHER_ESP32':
                print('feather device found!!!')
                async with BleakClient(d.address) as client:
                    print(f'BLE connected to {d.address}')
                    # for _ in range(10):
                        # val = await client.read_gatt_char(CURRENTSENSING_UUID)
                        # print('Motor read = ', val)
                        # current_zero += int(val)
                        # await asyncio.sleep(0.2)
                    # current_zero /= 10
                    # print(f'average at zero current = {current_zero}')
                    # await asyncio.sleep(1)
                    await setMotor(client)


asyncio.run(main())