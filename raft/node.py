import asyncio
import sys
import ujson
import logging
from codecs import StreamReader,StreamWriter
from typing import Dict, List, Tuple

PRIMARY = 'primary'
SECONDARY = 'secondary'
NO_IDEA = 'no_idea'
UNAVAILABLE = 'unavailable'

class Node():
    def __init__(self,host:str,
                port:int,
                peers = {}) -> None:
        self.host = host
        self.port = port
        self.name = host+':'+str(port)
        peers.update({self.name:NO_IDEA})
        self.peers = peers

    def __repr__(self) -> str:
        return self.name

    async def _loop_server(self, message, server_map ) :
        result = await asyncio.gather(
            *[self.send_msg(
                message=message,
                server_name = name
                ) for name,status in server_map.items()
                ], return_exceptions=True
            )
        return result

    async def send_msg(self,message:str,
                        server_name:str):
        if server_name == self.name:
            await asyncio.sleep(0.01)
            return f'{server_name}','pong'
        else:
            try:
                host,port = server_name.split(':')
                reader, writer = await asyncio.open_connection(host,port)
                writer.write(str.encode(f'{self.name}=>{message}'))
                await writer.drain()
                data = await reader.read(255)
                return f'{host}:{port}',data.decode('utf8')
            except Exception as e:
                logging.error(f'No response from server {e}')
                return f'{host}:{port}',f'{UNAVAILABLE} :: {e}'

    async def handle_client(self,
                        reader:StreamReader,
                        writer:StreamWriter) -> None:
        request = None
        while True:
            source_request = (await reader.read(255)).decode('utf8').lower()
            if not source_request:
                continue
            logging.info('source_request=>'+source_request)
            source,request = source_request.split('=>')

            if request == 'quit':
                logging.info('Disconnecting Client')
                response = 'Disconnecting'
                break

            elif request.startswith('join'):
                if self.peers[self.name] == PRIMARY:
                    command,data = request.strip().split(' ')
                    logging.info(f'Checking if server responds {data}')
                    server_name ,server_res = await self.send_msg(message='ping',
                                                    server_name = data )
                    if server_res == 'pong':
                        logging.info(f'Server responded with pong {data}')
                        set_status= NO_IDEA
                        if [key for key,value in self.peers.items() if value == PRIMARY ]:
                            set_status= SECONDARY
                        self.peers[data] = set_status
                        server_name ,server_res = await self.send_msg(
                                message=f'new_join_peers|{ujson.dumps(self.peers)}',
                                server_name=data)
                        other_server = { k:v for k,v in self.peers.items() if k != data }
                        await self._loop_server(
                            message=f'update_server {data} {set_status}', server_map = other_server)
                        response = 'Server joined the network'
                        logging.info(f'Server joined the network {data}')
                    else:
                        response = 'Server did not respond with pong'
                        logging.warning(f'Server did not respond with pong {data}')
                else:
                    respond = 'Only primary can add'
            elif request.startswith('ping'):
                response = 'pong'

            elif request.startswith('server'):
                response = self.name

            elif request.startswith('peers_list'):
                response = ujson.dumps(self.peers)

            elif request.startswith('check_peers'):
                result = await self._loop_server(message='ping',server_map= self.peers)
                response =  ujson.dumps(result)

            elif request.startswith('new_join_peers'):
                command, peers = request.split('|')
                self.peers = ujson.loads(peers)
                response = f'Send the existing peers data to new joining peers'

            elif request.startswith('make'):
                command, server_type, server_name = request.strip().split(' ')
                if server_type.lower() == PRIMARY:
                    logging.info(f'making primary {server_type} and {server_name}')
                    if primary_server := [key for key,value in self.peers.items() if value == PRIMARY ]:
                        response = f'Primary already avaliable {primary_server}'
                    else:
                        self.peers[server_name] = PRIMARY
                        for name,status in self.peers.items():
                            if status == NO_IDEA:
                                self.peers[self.name] = SECONDARY
                        result = await self._loop_server(
                                message=f'primary_sync {self.peers[self.name]} {ujson.dumps(self.peers)}',
                                server_map = self.peers)
                        response = f'Added server details to all servers {ujson.dumps(self.peers)}'
                else:
                    response = f'Only primary server can do primary sync'
                    logging.info(f'Only primary server can do primary sync')

            elif request.startswith('primary_sync'):
                command,server_status,servers = request.split(' ')
                if server_status == PRIMARY:
                    self.peers = ujson.loads(servers)
                    response = f'Adding all server data...'
                else:
                    response = f'Only primary server can do primary sync'
            elif request.startswith('update server'):
                command, server_details, server_status = request.strip().split(' ')
                self.peers[server_details] = server_status
                logging.info(f'Updating {server_details} {server_status}')
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
            beat_peer = {}
            server_status = await self._loop_server( message='ping',server_map=self.peers)
            logging.info('Heart beat')
            for name,status in server_status:
                if status.startswith(UNAVAILABLE):
                    logging.error('heartbeat failed for => {name} removing...')
                    beat_peer[name] = UNAVAILABLE
                    continue
                elif status == 'pong':
                    beat_peer[name] = 'pong'

            logging.info(f'heart beat status {str(beat_peer)} =={ str(self.peers)}')

            await asyncio.sleep(10)

    async def run_server_heartbeat(self):
        server_task = asyncio.create_task(self.run_server())
        # heart_beat = asyncio.create_task(self.heart_beat())
        await server_task
        # await heart_beat


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


