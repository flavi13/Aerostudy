import asyncio
import json
import random
import string
import time

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

FLIGHTS = {
    "MAD-TYO": {"name": "Madrid → Tokio",         "duration": 43200, "emoji": "🗼"},
    "MAD-NYC": {"name": "Madrid → New York",      "duration": 25200, "emoji": "🗽"},
    "MAD-SYD": {"name": "Madrid → Sydney",        "duration": 68400, "emoji": "🦘"},
    "BCN-LON": {"name": "Barcelona → London",     "duration": 7200,  "emoji": "🎡"},
    "MAD-CDG": {"name": "Madrid → Paris",         "duration": 4500,  "emoji": "🗼"},
    "MAD-FCO": {"name": "Madrid → Rome",          "duration": 5400,  "emoji": "🏛️"},
    "MAD-DXB": {"name": "Madrid → Dubai",         "duration": 21600, "emoji": "🌆"},
    "CUSTOM":  {"name": "Custom Flight",          "duration": 3600,  "emoji": "✈️"},
}

SEAT_COLORS = [
    "#1a3050",  # azul
    "#1a3530",  # verde
    "#3a1a35",  # púrpura
    "#3a2a1a",  # ámbar
    "#1a2a3a",  # gris azul
    "#2a1a1a",  # coral oscuro
]

rooms: dict[str, "StudyRoom"] = {}


def make_code():
    while True:
        code = "".join(random.choices(string.ascii_uppercase, k=4))
        if code not in rooms:
            return code


class StudyRoom:
    def __init__(self, flight_id: str, custom_duration: int = 0):
        if flight_id not in FLIGHTS:
            flight_id = "CUSTOM"
        f = FLIGHTS[flight_id]
        self.flight_id = flight_id
        self.flight_name = f["name"]
        self.duration = custom_duration if flight_id == "CUSTOM" else f["duration"]
        self.started_at = time.time()
        self.passengers: dict[WebSocket, dict] = {}
        self.connections: list[WebSocket] = []
        self.messages: list[dict] = []
        self.color_index = 0

    @property
    def elapsed(self):
        return time.time() - self.started_at

    @property
    def remaining(self):
        return max(0.0, self.duration - self.elapsed)

    @property
    def landed(self):
        return self.remaining <= 0

    @property
    def phase(self):
        pct = self.elapsed / self.duration
        if pct < 0.05:
            return "takeoff"
        elif pct < 0.15:
            return "ascend"
        elif pct < 0.85:
            return "crucero"
        elif pct < 0.95:
            return "descend"
        else:
            return "land"

    def next_color(self):
        c = SEAT_COLORS[self.color_index % len(SEAT_COLORS)]
        self.color_index += 1
        return c

    def assign_seat(self):
        taken = {p["seat"] for p in self.passengers.values()}
        for row in range(1, 20):
            for col in "ABCDEF":
                seat = f"{row}{col}"
                if seat not in taken:
                    return seat
        return "20A"

    def snapshot(self):
        pct = min(100, round((self.elapsed / self.duration) * 100))
        return {
            "type": "state",
            "flight_name": self.flight_name,
            "remaining": int(self.remaining),
            "duration": self.duration,
            "elapsed": int(self.elapsed),
            "progress_pct": pct,
            "phase": self.phase,
            "landed": self.landed,
            "passengers": list(self.passengers.values()),
            "messages": self.messages[-30:],
        }

    async def broadcast(self, data: dict):
        text = json.dumps(data)
        dead = []
        for ws in list(self.connections):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._remove(ws)

    def _remove(self, ws: WebSocket):
        self.connections = [c for c in self.connections if c is not ws]
        self.passengers.pop(ws, None)


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/room/{code}")
async def room_page(code: str):
    if code not in rooms:
        return HTMLResponse("<h2>Sala no encontrada</h2>", status_code=404)
    return FileResponse("static/cabin.html")


@app.post("/create")
async def create_room(data: dict):
    flight_id = data.get("flight_id", "MAD-TYO")
    custom_min = int(data.get("custom_minutes", 60))
    custom_sec = custom_min * 60
    code = make_code()
    rooms[code] = StudyRoom(flight_id, custom_sec)
    return {"code": code, "flight": rooms[code].flight_name}


@app.get("/flights")
async def get_flights():
    return FLIGHTS


@app.websocket("/ws/{room_code}/{player_name}")
async def ws_endpoint(ws: WebSocket, room_code: str, player_name: str):
    await ws.accept()

    if room_code not in rooms:
        await ws.send_text(json.dumps({"type": "error", "msg": "Sala no encontrada"}))
        await ws.close()
        return

    room = rooms[room_code]
    color = room.next_color()
    seat = room.assign_seat()

    room.passengers[ws] = {
        "name": player_name,
        "seat": seat,
        "color": color,
        "studying": True,
        "study_seconds": 0,
        "joined_at": time.time(),
    }
    room.connections.append(ws)
    room.messages.append({"sys": True, "text": f"{player_name} ha subido al avión ✈️"})

    await room.broadcast(room.snapshot())

    last_tick = time.time()

    async def ticker():
        nonlocal last_tick
        while ws in room.passengers:
            await asyncio.sleep(1)
            now = time.time()
            dt = now - last_tick
            last_tick = now
            p = room.passengers.get(ws)
            if p and p["studying"]:
                p["study_seconds"] += dt
            await room.broadcast(room.snapshot())
            if room.landed:
                break

    tick_task = asyncio.create_task(ticker())

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            if msg["type"] == "toggle_study":
                p = room.passengers.get(ws)
                if p:
                    p["studying"] = not p["studying"]
                    status = "estudiando" if p["studying"] else "ha pausado"
                    room.messages.append({"sys": True, "text": f"{player_name} {status}"})

            elif msg["type"] == "chat":
                text = str(msg.get("text", "")).strip()[:200]
                if text:
                    room.messages.append({"name": player_name, "color": color, "text": text})

            await room.broadcast(room.snapshot())

    except WebSocketDisconnect:
        pass
    finally:
        tick_task.cancel()
        name = room.passengers.get(ws, {}).get("name", player_name)
        room._remove(ws)
        room.messages.append({"sys": True, "text": f"{name} ha abandonado el vuelo"})
        await room.broadcast(room.snapshot())


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
