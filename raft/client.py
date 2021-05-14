import asyncio
import aiohttp

SERVER_ADDRESS = ('localhost', 9000)

event_loop = asyncio.get_event_loop()

async def echo_client(address):
    reader, writer = await asyncio.open_connection(*address)
    while True:
        command = input('command=')
        if command:
            writer.write(str.encode(command))
            await writer.drain()

            print('waiting for response')

            data = await reader.read(255)
            if data:
                print('received {!r}'.format(data))
            else:
                print('closing')
                writer.close()
                return

try:
    event_loop.run_until_complete(
        echo_client(SERVER_ADDRESS)
    )
finally:
    print('closing event loop')
    event_loop.close()