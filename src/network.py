import socket
import threading
import json
import time
from typing import Dict, List, Optional

class P2PNetwork:
    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        self.host = host
        self.port = port
        self.peers: Dict[str, float] = {}  # peer_address -> last_seen timestamp
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host, port))
        self.running = False
        
    def start(self):
        """Start the P2P network node"""
        self.running = True
        self.listen_thread = threading.Thread(target=self._listen)
        self.heartbeat_thread = threading.Thread(target=self._heartbeat)
        self.listen_thread.start()
        self.heartbeat_thread.start()

    def stop(self):
        """Stop the P2P network node"""
        self.running = False
        self.listen_thread.join()
        self.heartbeat_thread.join()
        self.socket.close()

    def _listen(self):
        """Listen for incoming messages from peers"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                message = json.loads(data.decode())
                
                if message['type'] == 'discovery':
                    self._handle_discovery(addr)
                elif message['type'] == 'heartbeat':
                    self._handle_heartbeat(addr)
                
            except Exception as e:
                print(f'Error in listen loop: {e}')

    def _heartbeat(self):
        """Send periodic heartbeats to peers and clean up stale peers"""
        while self.running:
            current_time = time.time()
            
            # Send heartbeat to all known peers
            message = json.dumps({'type': 'heartbeat'}).encode()
            for peer in list(self.peers.keys()):
                try:
                    host, port = peer.split(':')
                    self.socket.sendto(message, (host, int(port)))
                except Exception as e:
                    print(f'Error sending heartbeat to {peer}: {e}')

            # Remove peers that haven't been seen in 30 seconds
            stale_peers = [
                peer for peer, last_seen in self.peers.items()
                if current_time - last_seen > 30
            ]
            for peer in stale_peers:
                del self.peers[peer]

            time.sleep(10)  # Heartbeat interval

    def _handle_discovery(self, addr):
        """Handle incoming peer discovery request"""
        peer_addr = f'{addr[0]}:{addr[1]}'
        self.peers[peer_addr] = time.time()
        
        # Send back list of known peers
        response = json.dumps({
            'type': 'discovery_response',
            'peers': list(self.peers.keys())
        }).encode()
        self.socket.sendto(response, addr)

    def _handle_heartbeat(self, addr):
        """Handle incoming heartbeat from peer"""
        peer_addr = f'{addr[0]}:{addr[1]}'
        self.peers[peer_addr] = time.time()

    def broadcast(self, message: dict):
        """Broadcast a message to all known peers"""
        encoded_message = json.dumps(message).encode()
        for peer in self.peers:
            try:
                host, port = peer.split(':')
                self.socket.sendto(encoded_message, (host, int(port)))
            except Exception as e:
                print(f'Error broadcasting to {peer}: {e}')

    def discover_peers(self, bootstrap_nodes: List[tuple]):
        """Discover peers using bootstrap nodes"""
        message = json.dumps({'type': 'discovery'}).encode()
        for node in bootstrap_nodes:
            try:
                self.socket.sendto(message, node)
            except Exception as e:
                print(f'Error discovering peers from {node}: {e}')

    @property
    def peer_count(self) -> int:
        """Get the current number of active peers"""
        return len(self.peers)

    @property
    def active_peers(self) -> List[str]:
        """Get list of currently active peer addresses"""
        return list(self.peers.keys())