import asyncio
import sys
import ujson
import logging
from codecs import StreamReader,StreamWriter
from typing import Counter, Dict, List, Tuple
import time
PRIMARY = 'primary'
SECONDARY = 'secondary'
NO_IDEA = 'no_idea'
UNAVAILABLE = 'unavailable'


class Node:
    def __init__(
            self,name:str,host:str,port:int,status:str
        ) -> None:
        self.name = name
        self.host = host
        self.port = port
        self.status = status
        self.peers = {}
        self.peers[self.host+str(self.port)] = {
            'name': self.name,
            'host':self.host,
            'port':self.port,
            'status': self.status
        }

    def __repr__(self) -> str:
        return f'{self.host}:{self.port}'

    async def _loop_conn(self,servers:set,message:str):
        result = await asyncio.gather(
            *[self.send_msg(
                message=message,
                server = server
                ) for server in servers
                ], return_exceptions=True
            )
        return result

    async def _internal_request(self,command) -> str:
        if command.startswith('ping'):
            action_server = command.strip().split(' ')
            if len(action_server) > 1:
                action,server = action_server[0],set(action_server[1:])
                return await self._loop_conn(servers=server,message='ping')
            return 'pong'
    async def _client_request(command):
        pass

    async def handle_client(
        self,reader:StreamReader,writer:StreamWriter
        ) -> None:
        while True:
            recieved_data = (await reader.read(255)).decode('utf8').lower()
            logging.info(f'Data recieve while True: {str(recieved_data)}')
            recieved_data = ujson.dumps(recieved_data)
            source,command = recieved_data['source'], recieved_data['command']
            if not command:
                writer.write(''.encode('utf8'))
                await writer.drain()
                data = await reader.read(255)
                continue
            logging.info(f'handle_client() : {recieved_data}')
            if source.startswith('client'):
                response = await self._internal_request(command)
            else:
                respone = await self._client_request(command)
            writer.write(response.encode('utf8'))
            await writer.drain()
            data = await reader.read(255)


    async def run_server(self):
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port,self.name,self.status
            )
        await server.serve_forever()

    async def run_server_heartbeat(self):
        server_task = asyncio.create_task(self.run_server())
        # heart_beat = asyncio.create_task(self.heart_beat())
        await server_task
        logging.info(f'Running Server')
        # await heart_beat
        # logging.info(f'Heart beat')


async def main(port):
    node = Node(name='amod',host='localhost',port=8000,status=PRIMARY)
    await node.run_server_heartbeat()

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.basicConfig(format='%(levelname)s  %(asctime)s  %(message)s',
                         datefmt='%I:%M:%S')
                    #    datefmt='%d/%m/%Y %I:%M:%S %p')
    asyncio.run(main(sys.argv[1])