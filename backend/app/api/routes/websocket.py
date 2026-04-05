"""
WebSocket routes for real-time stock price streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.connection_manager import manager
from app.ws.price_streamer import streamer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/stocks/{symbol}")
async def websocket_stock_price(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for streaming real-time stock prices.
    
    Path: /ws/stocks/{symbol}
    
    Example:
        ws://localhost:8000/ws/stocks/AAPL
    
    Receives:
        {
            "symbol": "AAPL",
            "price": 180.25,
            "high": 182.50,
            "low": 179.80,
            "volume": 45000000,
            "timestamp": "2026-01-01T12:00:00Z"
        }
    """
    
    # Validate symbol format (basic validation)
    if not symbol or len(symbol) > 5 or not symbol.isalpha():
        await websocket.close(code=1008, reason="Invalid symbol format")
        return
    
    symbol = symbol.upper()
    
    try:
        # Connect this client
        await manager.connect(websocket, symbol)
        
        # Start streaming for this symbol if not already streaming
        stream_task_name = f"stream_{symbol}"
        if stream_task_name not in streamer.get_active_streams():
            await streamer.start_streaming(
                symbol,
                callback=manager.broadcast,
                task_name=stream_task_name
            )
        
        logger.info(f"WebSocket connected for {symbol}")
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Receive any messages from client (e.g., heartbeat)
                data = await websocket.receive_text()
                logger.debug(f"Received message from {symbol}: {data}")
            except WebSocketDisconnect:
                break
    
    except Exception as e:
        logger.error(f"WebSocket error for {symbol}: {e}")
    
    finally:
        # Clean up on disconnect
        await manager.disconnect(websocket, symbol)
        
        # Stop streaming if no more clients for this symbol
        if manager.get_connection_count(symbol) == 0:
            stream_task_name = f"stream_{symbol}"
            await streamer.stop_streaming(stream_task_name)
            logger.info(f"Stopped streaming {symbol} - no active connections")


@router.get("/status")
async def websocket_status():
    """
    Get status of WebSocket connections and active price streams.
    """
    return {
        "active_symbols": manager.get_all_symbols(),
        "connection_counts": {
            symbol: manager.get_connection_count(symbol)
            for symbol in manager.get_all_symbols()
        },
        "active_streams": streamer.get_active_streams(),
        "total_connections": sum(
            manager.get_connection_count(symbol)
            for symbol in manager.get_all_symbols()
        ),
    }
