import asyncio
import random
import websockets

PEER_DISCOVERY_INTERVAL = 60  # Seconds between peer discovery attempts
PEER_CONNECT_TIMEOUT = 10  # Seconds to wait for peer connection

class PeerNetwork:
    def __init__(self, data_marketplace):
        self.data_marketplace = data_marketplace
        self.peers = []
        self.running = False

    async def start(self):
        self.running = True
        await self.discover_peers()
        await self.maintain_connections()

    async def stop(self):
        self.running = False
        await asyncio.gather(*[peer.close() for peer in self.peers])

    async def discover_peers(self):
        while self.running:
            try:
                # Connect to known bootstrap nodes to discover more peers
                async with websockets.connect('ws://bootstrap1.decentralized-data-marketplace.com') as ws:
                    await ws.send(f'DISCOVER {self.data_marketplace.node_id}')
                    peers = await ws.recv()
                    self.peers.extend(peers.split(','))
            except Exception as e:
                print(f'Error discovering peers: {e}')
            await asyncio.sleep(PEER_DISCOVERY_INTERVAL)

    async def maintain_connections(self):
        while self.running:
            # Randomly connect to a few peers to maintain the network
            for _ in range(3):
                if self.peers:
                    peer = random.choice(self.peers)
                    try:
                        async with websockets.connect(f'ws://{peer}') as ws:
                            await ws.send(f'CONNECT {self.data_marketplace.node_id}')
                            # Perform handshake and add peer to active connections
                            self.peers.append(peer)
                    except Exception as e:
                        print(f'Error connecting to peer {peer}: {e}')
                        self.peers.remove(peer)
            await asyncio.sleep(PEER_CONNECT_TIMEOUT)
