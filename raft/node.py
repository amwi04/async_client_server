import asyncio
import sys
from random import randint
import logging
from codecs import StreamReader,StreamWriter
from typing import Dict, List, Tuple

PRIMARY = 'primary'
SECONDARY = 'secondary'
NO_IDEA = 'no_idea'

class Node():
    def __init__(self,host:str,
                port:int,
                peers={}) -> None:
        self.host = host
        self.port = port
        self.name = host+':'+str(port)
        self.peers = peers.update({self.name:NO_IDEA})

    async def _loop_server(self,server_map ) :
        result = await asyncio.gather(self.send_msg(
                message='ping',
                host=host,port=port
                ) for name,(host,port) in server_map.items())
        return result

    async def send_msg(self,message:str,
                        host:str,port:int):
        if f'{host}:{port}' == self.name:
            return f'{host}:{port}','pong'
        else:
            try:
                reader, writer = await asyncio.open_connection(host,port)
                writer.write(str.encode(f'{self.name}=>{message})'))
                await writer.drain()
                data = await reader.read(255)
                return f'{host}:{port}',data.decode('utf8')
            except Exception as e:
                logging.error(f'No response from server {e}')
                return f'{host}:{port}',f'Error {e}'

    async def handle_client(self,
                        reader:StreamReader,
                        writer:StreamWriter) -> None:
        request = None
        while True:
            source_request = (await reader.read(255)).decode('utf8').lower()
            logging.info('source_request=>'+source_request)
            source,request = source_request.split('=>')
            if request == 'quit':
                logging.info('Disconnecting Client')
                response = 'Disconnecting'
                break
            elif request.startswith('join'):
                command,data = request.strip().split(' ')
                host,port = data.split(':')
                server_name ,server_res = await self.send_msg(message='ping',
                                                 host=host,port=int(port))
                logging.error( server_res)
                if server_res == 'pong':
                    self.peers[host+':'+port] = 'Secondary'
                    response = 'Server joined the network'
                    logging.info(f'Server joined the network {host}:{port}')
                else:
                    response = 'Server did not respond with pong'
                    logging.warning(f'Server did not respond with pong {host}:{port}')
            elif request.startswith('ping'):
                response = 'pong'
            elif request.startswith('server'):
                response = self.name
            elif request.startswith('peers_list'):
                response = str(self.peers)
            elif request.startswith('check_peers'):
                response = str(self.peers)
            else:
                response = str(f'Got request {request}')
            logging.info('response=>'+response)
            writer.write(response.encode('utf8'))
            await writer.drain()
        writer.close()


    async def run_server(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        await server.serve_forever()

    async def heart_beat(self) -> None:
        while True:
            server_status = await self._loop_server(self.peers)
            for name,status in server_status:
                self.peers[name] = status
            await asyncio.sleep(10)

    async def run_server_heartbeat(self):
        server_task = asyncio.create_task(self.run_server())
        heart_beat = asyncio.create_task(self.heart_beat())
        await server_task
        await heart_beat


async def main(port):
    host,port = 'localhost',port
    node = Node(host=host,port=port,peers={})
    logging.info(f'Server is about to start on {host}:{port}')
    await node.run_server_heartbeat()

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.basicConfig(format='%(levelname)s  %(asctime)s  %(message)s',
                        datefmt='%d/%m/%Y %I:%M:%S %p')
    asyncio.run(main(sys.argv[1]))


