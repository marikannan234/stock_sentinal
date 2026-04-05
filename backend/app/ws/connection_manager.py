"""
WebSocket connection manager for handling multiple client connections
and broadcasting price updates to subscribed clients.
"""

import asyncio
import json
from typing import Set, Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts price updates.
    Supports pub-sub pattern - multiple clients subscribing to price updates for a symbol.
    """

    def __init__(self):
        # Structure: { symbol: set(websockets) }
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Cache latest price for each symbol: { symbol: { "price": float, "timestamp": str } }
        self.price_cache: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, symbol: str):
        """Accept a new WebSocket connection for a symbol."""
        await websocket.accept()
        
        if symbol not in self.active_connections:
            self.active_connections[symbol] = set()
        
        self.active_connections[symbol].add(websocket)
        logger.info(f"Client connected to {symbol}. Active: {len(self.active_connections[symbol])}")
        
        # Send cached price immediately if available
        if symbol in self.price_cache:
            await self.send_cached_price(websocket, symbol)

    async def disconnect(self, websocket: WebSocket, symbol: str):
        """Remove a WebSocket connection."""
        if symbol in self.active_connections:
            self.active_connections[symbol].discard(websocket)
            logger.info(f"Client disconnected from {symbol}. Active: {len(self.active_connections[symbol])}")
            
            # Clean up empty entries
            if not self.active_connections[symbol]:
                del self.active_connections[symbol]

    async def send_cached_price(self, websocket: WebSocket, symbol: str):
        """Send cached price to a single client."""
        if symbol in self.price_cache:
            try:
                await websocket.send_json({
                    "symbol": symbol,
                    **self.price_cache[symbol]
                })
            except Exception as e:
                logger.error(f"Error sending cached price: {e}")

    async def broadcast(self, symbol: str, price_data: dict):
        """
        Broadcast price update to all clients connected to a symbol.
        Updates cache and sends to all active connections.
        """
        async with self._lock:
            # Update cache
            self.price_cache[symbol] = price_data
        
        if symbol not in self.active_connections:
            return
        
        # Send to all connected clients
        disconnected_clients = []
        for websocket in self.active_connections[symbol]:
            try:
                await websocket.send_json({
                    "symbol": symbol,
                    **price_data
                })
            except Exception as e:
                logger.warning(f"Error broadcasting to client: {e}")
                disconnected_clients.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected_clients:
            await self.disconnect(websocket, symbol)

    async def broadcast_to_all(self, data: dict):
        """Broadcast a message to all connected clients across all symbols."""
        for symbol in list(self.active_connections.keys()):
            await self.broadcast(symbol, data)

    def get_connection_count(self, symbol: str) -> int:
        """Get number of active connections for a symbol."""
        return len(self.active_connections.get(symbol, set()))

    def get_all_symbols(self) -> list:
        """Get all symbols with active connections."""
        return list(self.active_connections.keys())


# Global connection manager instance
manager = ConnectionManager()
