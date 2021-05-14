import asyncio, aiohttp, sys
from random import randint
import logging
from codecs import StreamReader,StreamWriter

class Node():
    def __init__(self,host:str,
                port:int,is_master=True,
                peers={}) -> None:
        self.host = host
        self.port = port
        self.name = host+':'+str(port)
        self.is_master = is_master
        self.peers = peers

    async def check_peers(self) -> None:
        peer = {}
        for name,(host,port) in self.peers.items():
            server_res = await self.send_msg(message='ping',host=host,port=port)
            if server_res == 'Error':
                logging.error(f'Server not reachable removing from peers => {name}')
                continue
            peer[name] = [host,port]
        self.peers = peer

    async def send_msg(self,message:str,
                        host:str,port:int) -> str:
        try:
            reader, writer = await asyncio.open_connection(host,port)
            writer.write(str.encode(message))
            await writer.drain()
            data = await reader.read(255)
            return data.decode('utf8')
        except Exception as e:
            logging.error('No response from server')
            return 'Error'

    async def handle_client(self,
                        reader:StreamReader,
                        writer:StreamWriter) -> None:
        request = None
        while True:
            request = (await reader.read(255)).decode('utf8').lower()
            logging.info('request=>'+request)
            if request == 'quit':
                logging.info('Disconnecting Client')
                response = 'Disconnecting'
                break
            elif request.startswith('join'):
                command,data = request.strip().split(' ')
                host,port = data.split(':')
                logging.info('join host:port =>' + data )
                server_res = await self.send_msg(message='ping',
                                                 host=host,port=int(port))
                logging.info('join server response='+server_res)
                if server_res == 'pong':
                    self.peers[host+':'+port] = [host,int(port)]
                    response = 'Server joined the network'
                else:
                    response = 'Server did not respond with pong'
            elif request.startswith('ping'):
                response = 'pong'
            elif request.startswith('server'):
                response = self.name
            elif request.startswith('peers_list'):
                response = str(self.peers)
            elif request.startswith('check_peers'):
                await self.check_peers()
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

async def main(port):
    host,port = 'localhost',port
    node = Node(host=host,port=port,peers={'localhost:8000':['localhost',8000]})
    logging.info(f'Server is about to start on {host}:{port}')
    await node.run_server()



if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.basicConfig(format='%(levelname)s  %(asctime)s  %(message)s',
                        datefmt='%d/%m/%Y %I:%M:%S %p')
    asyncio.run(main(sys.argv[1]))