import asyncio
from typing import Dict, List, Set
from kademlia.network import Server
from dataclasses import dataclass
import json
import time

@dataclass
class PeerInfo:
    node_id: str
    ip: str
    port: int
    last_seen: float
    capabilities: List[str]

class DecentralizedNetwork:
    def __init__(self, bootstrap_nodes=None):
        self.server = Server()
        self.bootstrap_nodes = bootstrap_nodes or []
        self.peers: Dict[str, PeerInfo] = {}
        self.node_id = None
        self._shutdown = False

    async def start(self, port: int):
        """Start the network node and connect to bootstrap peers"""
        await self.server.listen(port)
        self.node_id = self.server.node.long_id
        
        if self.bootstrap_nodes:
            await self.server.bootstrap(self.bootstrap_nodes)
        
        asyncio.create_task(self._periodic_peer_discovery())

    async def stop(self):
        """Gracefully shutdown the network node"""
        self._shutdown = True
        await self.server.stop()

    async def _periodic_peer_discovery(self):
        """Continuously discover and maintain peer connections"""
        while not self._shutdown:
            try:
                # Discover new peers
                peers_data = await self.server.get('peers')
                if peers_data:
                    discovered = json.loads(peers_data)
                    self._update_peers(discovered)

                # Advertise self
                self_info = PeerInfo(
                    node_id=str(self.node_id),
                    ip='127.0.0.1',  # TODO: Get actual public IP
                    port=self.server.port,
                    last_seen=time.time(),
                    capabilities=['data_exchange', 'storage']
                )
                
                current_peers = {**self.peers}
                current_peers[str(self.node_id)] = self_info
                await self.server.set('peers', json.dumps(current_peers))

                # Prune stale peers
                self._prune_stale_peers()

            except Exception as e:
                print(f"Peer discovery error: {e}")

            await asyncio.sleep(60)  # Run discovery every minute

    def _update_peers(self, discovered_peers: Dict):
        """Update local peer registry with discovered peers"""
        for peer_id, peer_data in discovered_peers.items():
            if peer_id not in self.peers:
                self.peers[peer_id] = PeerInfo(**peer_data)
            else:
                # Update last_seen for existing peers
                self.peers[peer_id].last_seen = time.time()

    def _prune_stale_peers(self, max_age: int = 300):
        """Remove peers that haven't been seen for max_age seconds"""
        current_time = time.time()
        stale_peers = [
            peer_id for peer_id, peer in self.peers.items()
            if current_time - peer.last_seen > max_age
        ]
        for peer_id in stale_peers:
            del self.peers[peer_id]

    async def broadcast(self, message: str):
        """Broadcast a message to all connected peers"""
        for peer in self.peers.values():
            try:
                await self.server.set(f"msg:{peer.node_id}", message)
            except Exception as e:
                print(f"Failed to broadcast to {peer.node_id}: {e}")

    async def get_network_size(self) -> int:
        """Get the current number of active peers"""
        return len(self.peers) + 1  # Include self

    def get_active_peers(self) -> List[PeerInfo]:
        """Get list of currently active peers"""
        return list(self.peers.values())
