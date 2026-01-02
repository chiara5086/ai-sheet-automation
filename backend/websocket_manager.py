"""
WebSocket Manager for real-time progress updates
"""
from typing import Dict, Set
import json
import asyncio
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def has_active_connection(self, session_id: str) -> bool:
        """Check if there are any active WebSocket connections for a session"""
        if session_id not in self.active_connections:
            return False
        # Remove any closed connections
        active = set()
        for ws in self.active_connections[session_id]:
            if ws.client_state.name == 'CONNECTED':
                active.add(ws)
        self.active_connections[session_id] = active
        return len(active) > 0
    
    def get_active_sessions(self) -> list:
        """Get list of all active session IDs"""
        active_sessions = []
        for session_id, connections in list(self.active_connections.items()):
            # Clean up closed connections
            active = set()
            for ws in connections:
                if ws.client_state.name == 'CONNECTED':
                    active.add(ws)
            if active:
                active_sessions.append(session_id)
                self.active_connections[session_id] = active
            else:
                # Remove empty sessions
                del self.active_connections[session_id]
        return active_sessions
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            disconnected = set()
            sent_count = 0
            for connection in list(self.active_connections[session_id]):  # Use list to avoid modification during iteration
                try:
                    # Check if connection is still open
                    if connection.client_state.name == 'CONNECTED':
                        await connection.send_json(message)
                        sent_count += 1
                        print(f"DEBUG: Sent message to WebSocket connection (session: {session_id})", flush=True)
                    else:
                        print(f"DEBUG: WebSocket connection is not CONNECTED (state: {connection.client_state.name})", flush=True)
                        disconnected.add(connection)
                except Exception as e:
                    print(f"ERROR: Error broadcasting to connection: {e}", flush=True)
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections[session_id].discard(connection)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
            
            print(f"DEBUG: Broadcast complete - sent to {sent_count} connection(s), removed {len(disconnected)} disconnected", flush=True)
        else:
            print(f"DEBUG: No active connections found for session {session_id}", flush=True)

manager = ConnectionManager()

