"""
WebSocket connection manager for handling multiple client connections
and broadcasting price updates and alerts to subscribed clients.
With error recovery and graceful degradation.
"""

import asyncio
import json
from typing import Set, Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages WebSocket connections for real-time alert notifications.
    Broadcasts alerts to all connected users when they trigger.
    """
    
    def __init__(self):
        # Set of all WebSocket connections for alerts
        self.alert_subscribers: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def subscribe(self, websocket: WebSocket):
        """Add a client to alert subscribers."""
        try:
            async with self._lock:
                self.alert_subscribers.add(websocket)
            logger.debug(f"Client subscribed to alerts. Total subscribers: {len(self.alert_subscribers)}")
        except Exception as e:
            logger.error(f"Error subscribing to alerts: {e}")
            raise
    
    async def unsubscribe(self, websocket: WebSocket):
        """Remove a client from alert subscribers."""
        try:
            async with self._lock:
                self.alert_subscribers.discard(websocket)
            logger.debug(f"Client unsubscribed from alerts. Total subscribers: {len(self.alert_subscribers)}")
        except Exception as e:
            logger.warning(f"Error unsubscribing from alerts: {e}")
    
    async def broadcast_alert(self, alert_data: dict):
        """
        Broadcast an alert to all connected clients.
        
        Args:
            alert_data: Alert data dict with keys:
                - type: "alert" (required)
                - alert_id: Alert ID
                - symbol: Stock symbol
                - message: Human-readable message
                - current_price: Current stock price
                - target_value: Target price
                - condition: Alert condition
                - timestamp: When alert triggered
        """
        try:
            async with self._lock:
                disconnected_clients = []
                
                for websocket in list(self.alert_subscribers):
                    try:
                        await websocket.send_json(alert_data)
                        logger.debug(f"Alert sent: {alert_data.get('symbol')}")
                    except Exception as e:
                        logger.debug(f"Error sending alert to client: {e}")
                        disconnected_clients.append(websocket)
                
                # Remove disconnected clients
                for websocket in disconnected_clients:
                    self.alert_subscribers.discard(websocket)
                    
        except Exception as e:
            logger.error(f"Error in broadcast_alert: {e}")
    
    def get_subscriber_count(self) -> int:
        """Get number of alert subscribers."""
        return len(self.alert_subscribers)


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts price updates.
    Supports pub-sub pattern - multiple clients subscribing to price updates for a symbol.
    Implements error handling and graceful disconnection.
    """

    def __init__(self):
        # Structure: { symbol: set(websockets) }
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Cache latest price for each symbol: { symbol: { "price": float, "timestamp": str } }
        self.price_cache: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, symbol: str):
        """Accept a new WebSocket connection for a symbol."""
        try:
            await websocket.accept()
            
            if symbol not in self.active_connections:
                self.active_connections[symbol] = set()
            
            self.active_connections[symbol].add(websocket)
            logger.info(f"Client connected to {symbol}. Active: {len(self.active_connections[symbol])}")
            
            # Send cached price immediately if available
            if symbol in self.price_cache:
                await self.send_cached_price(websocket, symbol)
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {e}")
            raise

    async def disconnect(self, websocket: WebSocket, symbol: str):
        """Remove a WebSocket connection."""
        try:
            if symbol in self.active_connections:
                self.active_connections[symbol].discard(websocket)
                logger.info(f"Client disconnected from {symbol}. Active: {len(self.active_connections[symbol])}")
                
                # Clean up empty entries
                if not self.active_connections[symbol]:
                    del self.active_connections[symbol]
        except Exception as e:
            logger.warning(f"Error during disconnect for {symbol}: {e}")

    async def send_cached_price(self, websocket: WebSocket, symbol: str):
        """Send cached price to a single client."""
        if symbol in self.price_cache:
            try:
                await websocket.send_json({
                    "symbol": symbol,
                    **self.price_cache[symbol]
                })
            except Exception as e:
                logger.warning(f"Error sending cached price to client: {e}")

    async def broadcast(self, symbol: str, price_data: dict):
        """
        Broadcast price update to all clients connected to a symbol.
        Updates cache and sends to all active connections.
        Handles disconnected clients gracefully.
        """
        try:
            async with self._lock:
                # Update cache
                self.price_cache[symbol] = price_data
            
            if symbol not in self.active_connections:
                return
            
            # Send to all connected clients
            disconnected_clients = []
            for websocket in list(self.active_connections[symbol]):
                try:
                    await websocket.send_json({
                        "symbol": symbol,
                        **price_data
                    })
                except Exception as e:
                    logger.debug(f"Error broadcasting to client: {e}")
                    disconnected_clients.append(websocket)
            
            # Remove disconnected clients
            for websocket in disconnected_clients:
                await self.disconnect(websocket, symbol)
        
        except Exception as e:
            logger.error(f"Error in broadcast for {symbol}: {e}")

    async def broadcast_to_all(self, data: dict):
        """Broadcast a message to all connected clients across all symbols."""
        for symbol in list(self.active_connections.keys()):
            try:
                await self.broadcast(symbol, data)
            except Exception as e:
                logger.warning(f"Error broadcasting to {symbol}: {e}")

    def get_connection_count(self, symbol: str) -> int:
        """Get number of active connections for a symbol."""
        return len(self.active_connections.get(symbol, set()))

    def get_all_symbols(self) -> list:
        """Get all symbols with active connections."""
        return list(self.active_connections.keys())


# Global connection manager instance
manager = ConnectionManager()

# Global alert manager instance
alert_manager = AlertManager()
