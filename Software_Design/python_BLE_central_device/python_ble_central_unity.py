import socket
import asyncio
from bleak import BleakScanner, BleakClient
import json

MOTOR_UUID = 'f22535de-5375-44bd-8ca9-d0ea9ff9e410'

async def setMotor(client, socket_conn):
    while True:
        data = socket_conn.recv(1024)
        if not data:
            break
        print('TCP data recv = ', data)
        if len(data) > 420:
            print("long data! split!")
            # Split the data into chunks by "every seventh \n"
            data_str = data.decode('utf-8').strip()
            data_chunks = data_str.split("\n")
            for i in range(0, len(data_chunks), 7):
                if i < len(data_chunks)-7:
                    data_sent = "\n".join(data_chunks[i:i+7])
                else:
                    data_sent = "\n".join(data_chunks[i:])
                await client.write_gatt_char(MOTOR_UUID, data_sent.encode('utf-8'))
        else:
            await client.write_gatt_char(MOTOR_UUID, data)

async def main(socket_conn):
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
                    for i in range(8):
                        buck_addr = i*30
                        command = {
                            'addr':buck_addr, 
                            'mode':1,
                            'duty':1, # default
                            'freq':3, # default
                            'wave':1, # default
                        }
                        data = bytearray(json.dumps(command), 'utf-8')
                        print(data)
                        await client.write_gatt_char(MOTOR_UUID,  data)
                    while True:
                        await setMotor(client, socket_conn)

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 9051  # Port to listen on (non-privileged ports are > 1023)

while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        print('python server start listening')
        s.listen()
        conn, addr = s.accept()
        with conn:
            print(f"TCP socket connected by {addr}")
            # while True:
                # data = conn.recv(1024)
                # print('TCP data recv = ', data)
                # if not data:
                #     break
            asyncio.run(main(conn))
    print('TCP socket disconnected! restart now...')