"""
WebSocket manager for real-time alerts.

Broadcasts high-risk events to connected clients.
"""

import asyncio
import json
from typing import Set, Dict
from fastapi import WebSocket


class WebSocketManager:
    """Manage WebSocket connections and broadcast alerts."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.alert_history: list = []
        self.max_history = 50

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"[WebSocket] Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected client."""
        self.active_connections.discard(websocket)
        print(f"[WebSocket] Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        message["timestamp"] = asyncio.get_event_loop().time()

        # Store in history
        self.alert_history.append(message)
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]

        # Broadcast to all clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[WebSocket] Error sending to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_alert(self, alert_type: str, details: dict, risk_score: int):
        """Send a high-risk alert to all clients."""
        if risk_score < 5:
            return  # Only broadcast significant alerts

        message = {
            "type": "alert",
            "alert_type": alert_type,
            "risk_score": risk_score,
            "details": details
        }

        await self.broadcast(message)

    async def send_analysis_result(self, result: dict):
        """Send analysis result to all clients."""
        message = {
            "type": "analysis",
            "result": {
                "timestamp": result.get("timestamp"),
                "location": result.get("location"),
                "risk_score": result.get("risk_score"),
                "alerts": result.get("alerts", []),
                "object_counts": result.get("object_counts", {}),
                "anomalies": result.get("anomalies", [])
            }
        }

        await self.broadcast(message)

    def get_alert_history(self) -> list:
        """Return recent alert history."""
        return self.alert_history


# Global manager instance
ws_manager = WebSocketManager()
