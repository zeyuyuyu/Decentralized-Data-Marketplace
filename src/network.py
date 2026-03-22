import asyncio
import json
from typing import Dict, Set, Optional
from dataclasses import dataclass
import websockets

@dataclass
class Node:
    id: str
    address: str
    capabilities: Set[str]
    last_seen: float

class SwarmNetwork:
    def __init__(self, host: str = '0.0.0.0', port: int = 8765):
        self.host = host
        self.port = port
        self.nodes: Dict[str, Node] = {}
        self.node_id = None
        self.capabilities = set()
        self.running = False

    async def start(self, node_id: str, capabilities: Set[str]):
        self.node_id = node_id
        self.capabilities = capabilities
        self.running = True
        
        server = await websockets.serve(
            self.handle_connection, self.host, self.port
        )
        await self.discover_nodes()
        await server.wait_closed()

    async def discover_nodes(self):
        """Actively discover other nodes in the network"""
        while self.running:
            try:
                # Broadcast presence to known nodes
                for node in list(self.nodes.values()):
                    try:
                        async with websockets.connect(node.address) as ws:
                            await ws.send(json.dumps({
                                'type': 'discovery',
                                'node_id': self.node_id,
                                'capabilities': list(self.capabilities),
                                'address': f'ws://{self.host}:{self.port}'
                            }))
                    except:
                        # Remove stale nodes
                        del self.nodes[node.id]
                
                await asyncio.sleep(30)  # Discovery interval
            except Exception as e:
                print(f'Discovery error: {e}')
                await asyncio.sleep(5)

    async def handle_connection(self, websocket, path):
        """Handle incoming connections and messages"""
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data['type'] == 'discovery':
                    # Register new node
                    self.nodes[data['node_id']] = Node(
                        id=data['node_id'],
                        address=data['address'], 
                        capabilities=set(data['capabilities']),
                        last_seen=asyncio.get_event_loop().time()
                    )
                    
                    # Reply with our info
                    await websocket.send(json.dumps({
                        'type': 'discovery',
                        'node_id': self.node_id,
                        'capabilities': list(self.capabilities),
                        'address': f'ws://{self.host}:{self.port}'
                    }))
                    
                elif data['type'] == 'message':
                    # Handle regular messages
                    print(f'Received message from {data["source"]}: {data["content"]}')

        except Exception as e:
            print(f'Connection handler error: {e}')

    async def broadcast(self, message: str):
        """Broadcast message to all connected nodes"""
        for node in self.nodes.values():
            try:
                async with websockets.connect(node.address) as ws:
                    await ws.send(json.dumps({
                        'type': 'message',
                        'source': self.node_id,
                        'content': message
                    }))
            except Exception as e:
                print(f'Broadcast error to {node.id}: {e}')

    def get_nodes_with_capability(self, capability: str) -> Set[Node]:
        """Find nodes that have a specific capability"""
        return {node for node in self.nodes.values() 
                if capability in node.capabilities}

    async def stop(self):
        """Gracefully shutdown the network"""
        self.running = False
        # Notify other nodes
        await self.broadcast('Node disconnecting')
