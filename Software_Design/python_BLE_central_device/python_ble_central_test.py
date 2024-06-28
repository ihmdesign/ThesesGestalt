import asyncio
from bleak import BleakScanner, BleakClient
import json

MOTOR_UUID = 'f22535de-5375-44bd-8ca9-d0ea9ff9e410'

async def setMotor(client):
    while True:
        motor_addr = int(input('what is the next motor you want to control?'))
        if motor_addr % 30 == 0:
            duty = int(input('0-31 for intensity?'))
            start_or_stop = int(input('1 for start and 0 for stop?'))
            command = {
                'addr':motor_addr,
                'mode':start_or_stop,
                'duty':(duty>>3), # default
                'freq':(duty>>1) & 3, # default
                'wave':(duty & 1), # default
            }
        else:
            duty = int(input('0-15 for duty?'))
            start_or_stop = int(input('1 for start and 0 for stop?'))
            command = {
                'addr':motor_addr,
                'mode':start_or_stop,
                'duty':duty, # default
                'freq':2, # default
                'wave':0, # default
            }
        output = bytearray(json.dumps(command), 'utf-8')
        print(output)
        await client.write_gatt_char(MOTOR_UUID,  output)

async def main():
    devices = await BleakScanner.discover()
    for d in devices:
        print('device name = ', d.name)
        if d.name != None:
            if d.name == 'FEATHER_ESP32':
                print('feather device found!!!')
                async with BleakClient(d.address) as client:
                    print(f'BLE connected to {d.address}')
                    val = await client.read_gatt_char(MOTOR_UUID)
                    print('Motor read = ', val)
                    await setMotor(client)

asyncio.run(main())