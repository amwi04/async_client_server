import asyncio
import sys

async def handle_client(reader,writer):
    while True:
        recieved_data = (await reader.read(255)).decode('utf8').lower()
        writer.write(recieved_data.encode('utf8'))
        await writer.drain()
        # writer.close()
        # data = await reader.read(255)
        # print(data)

async def main(port):
    server = await asyncio.start_server(handle_client, 'localhost',port)
    async with server:
	    await server.serve_forever()

if __name__ == '__main__':
	asyncio.run(main(sys.argv[1]))