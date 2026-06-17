import asyncio
import json
import logging
from typing import Optional
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Global state: map room_id -> {connections, game_task, end_task, etc.}
_rooms: dict[str, dict] = {}

# Store player info (nickname) for rooms, keyed by room_id
game_state_store: dict[str, dict] = {}


class RoomConnectionManager:
    async def connect(self, room_id: str, player_id: str, ws: WebSocket):
        await ws.accept()
        if room_id not in _rooms:
            _rooms[room_id] = {
                "connections": {},
                "game_task": None,
                "end_task": None,
            }
        # 关闭旧连接（防止刷新页面后残留孤儿连接）
        old_ws = _rooms[room_id]["connections"].get(player_id)
        if old_ws:
            try:
                await old_ws.close(code=4000, reason="replaced by new connection")
            except Exception:
                pass
        _rooms[room_id]["connections"][player_id] = ws
        logger.info(f"Player {player_id} connected to room {room_id}")

    def disconnect(self, room_id: str, player_id: str):
        if room_id in _rooms:
            _rooms[room_id]["connections"].pop(player_id, None)
            if not _rooms[room_id]["connections"]:
                # No cleanup of game tasks here; game still runs in background
                pass
            logger.info(f"Player {player_id} disconnected from room {room_id}")

    async def broadcast(self, room_id: str, message: dict, exclude: Optional[str] = None):
        if room_id not in _rooms:
            return
        connections = _rooms[room_id]["connections"]
        if not connections:
            return
        text = json.dumps(message, ensure_ascii=False)
        tasks = []
        for pid, ws in connections.items():
            if pid == exclude:
                continue
            tasks.append(self._safe_send(ws, text))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_to(self, room_id: str, player_id: str, message: dict):
        if room_id not in _rooms:
            return
        ws = _rooms[room_id]["connections"].get(player_id)
        if ws:
            text = json.dumps(message, ensure_ascii=False)
            await self._safe_send(ws, text)

    def get_connections(self, room_id: str) -> dict[str, WebSocket]:
        return _rooms.get(room_id, {}).get("connections", {})

    def set_game_task(self, room_id: str, task: Optional[asyncio.Task]):
        if room_id in _rooms:
            _rooms[room_id]["game_task"] = task

    def set_end_task(self, room_id: str, task: Optional[asyncio.Task]):
        if room_id in _rooms:
            _rooms[room_id]["end_task"] = task

    def cancel_tasks(self, room_id: str):
        if room_id not in _rooms:
            return
        for key in ("game_task", "end_task"):
            t = _rooms[room_id].get(key)
            if t and not t.done():
                t.cancel()

    async def _safe_send(self, ws: WebSocket, text: str):
        try:
            await ws.send_text(text)
        except Exception:
            pass


manager = RoomConnectionManager()
