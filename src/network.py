import socket
import threading
import json
import time
from typing import List, Dict, Optional

class P2PNetwork:
    def __init__(self, port: int = 8000):
        self.port = port
        self.peers: Dict[str, float] = {}  # peer_address -> last_seen timestamp
        self.running = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', port))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
    def start(self):
        """Start the P2P network node"""
        self.running = True
        self.discovery_thread = threading.Thread(target=self._discover_peers)
        self.listen_thread = threading.Thread(target=self._listen)
        self.maintenance_thread = threading.Thread(target=self._maintain_peers)
        
        self.discovery_thread.start()
        self.listen_thread.start()
        self.maintenance_thread.start()

    def stop(self):
        """Stop the P2P network node"""
        self.running = False
        self.sock.close()
        
    def _discover_peers(self):
        """Periodically broadcast discovery messages"""
        while self.running:
            try:
                discovery_msg = {
                    'type': 'DISCOVERY',
                    'port': self.port,
                    'timestamp': time.time()
                }
                self.sock.sendto(json.dumps(discovery_msg).encode(), 
                               ('<broadcast>', self.port))
                time.sleep(10)  # Discovery interval
            except:
                continue

    def _listen(self):
        """Listen for incoming peer messages"""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                msg = json.loads(data.decode())
                
                if msg['type'] == 'DISCOVERY':
                    peer_addr = f'{addr[0]}:{msg["port"]}'
                    self.peers[peer_addr] = msg['timestamp']
                    
                    # Send acknowledgment
                    ack_msg = {
                        'type': 'ACK',
                        'port': self.port,
                        'timestamp': time.time()
                    }
                    self.sock.sendto(json.dumps(ack_msg).encode(), addr)
                    
                elif msg['type'] == 'ACK':
                    peer_addr = f'{addr[0]}:{msg["port"]}'
                    self.peers[peer_addr] = msg['timestamp']
                    
            except:
                continue

    def _maintain_peers(self):
        """Remove stale peers"""
        while self.running:
            try:
                current_time = time.time()
                stale_peers = [
                    addr for addr, last_seen in self.peers.items()
                    if current_time - last_seen > 30  # 30 second timeout
                ]
                for peer in stale_peers:
                    del self.peers[peer]
                time.sleep(5)
            except:
                continue

    def get_active_peers(self) -> List[str]:
        """Get list of currently active peers"""
        return list(self.peers.keys())

    def broadcast_message(self, message: dict):
        """Broadcast a message to all peers"""
        for peer in self.peers:
            try:
                host, port = peer.split(':')
                self.sock.sendto(json.dumps(message).encode(), 
                               (host, int(port)))
            except:
                continue

    def send_to_peer(self, peer: str, message: dict) -> bool:
        """Send a message to a specific peer"""
        try:
            host, port = peer.split(':')
            self.sock.sendto(json.dumps(message).encode(), 
                           (host, int(port)))
            return True
        except:
            return False