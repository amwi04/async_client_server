import asyncio
import sys

async def handle_client(reader,writer):
    while True:
        recieved_data = (await reader.read(255)).decode('utf8').lower()
        if not recieved_data:
            await asyncio.sleep(1)
            continue
        print(f'recieved_data {recieved_data}')
        # writer.write(recieved_data.encode('utf8'))
        # await writer.drain()  
        print(f'await drain() {writer}')
        # writer.close()
        # data = await reader.read(255)
        # print(data)

async def main(port):
    server = await asyncio.start_server(handle_client, 'localhost',port)
    print(f'starting server {port}')
    async with server:
	    await server.serve_forever()

if __name__ == '__main__':
	asyncio.run(main(sys.argv[1]),debug=True)