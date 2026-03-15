import asyncio
import json
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .ros_node import get_node, start_ros, stop_ros

STATIC_DIR = pathlib.Path(__file__).parent / "static"
VALID_MODES = {"STAND_BY", "PATROL", "MANUAL"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_ros()
    yield
    stop_ros()


app = FastAPI(lifespan=lifespan)


# ── REST: mode switching ───────────────────────────────────────────────────────

class ModeRequest(BaseModel):
    mode: str


@app.post("/api/mode")
async def set_mode(body: ModeRequest):
    if body.mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {body.mode}")
    loop = asyncio.get_running_loop()
    success, message = await loop.run_in_executor(
        None, get_node().call_mode_service, body.mode
    )
    if not success:
        raise HTTPException(status_code=500, detail=message)
    # Update locally even if the robot was already in this mode and skipped
    # publishing to the topic (volatile QoS, no re-publish on "already in mode")
    get_node().set_known_mode(body.mode)
    return {"success": True, "message": message}


@app.get("/api/mode")
async def get_mode():
    return {"mode": get_node().get_current_mode()}


# ── WebSocket: joystick streaming ─────────────────────────────────────────────

@app.websocket("/ws/joystick")
async def joystick_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            linear_x = float(payload.get("linear_x", 0.0))
            angular_z = float(payload.get("angular_z", 0.0))
            get_node().publish_joy(linear_x, angular_z)
    except WebSocketDisconnect:
        # Stop robot when browser disconnects
        get_node().publish_joy(0.0, 0.0)


# ── WebSocket: mode feedback ───────────────────────────────────────────────────

@app.websocket("/ws/mode")
async def mode_ws(websocket: WebSocket):
    await websocket.accept()
    last_mode = None
    try:
        while True:
            node = get_node()
            if node is not None:
                current = node.get_current_mode()
                if current != last_mode:
                    last_mode = current
                    await websocket.send_text(json.dumps({"mode": current}))
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        import logging
        logging.getLogger("mode_ws").error("mode_ws crashed: %s", exc)


# ── Static files (built React app) ────────────────────────────────────────────

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


# ── Entry point for `ros2 run` ────────────────────────────────────────────────

def ros_main():
    import uvicorn
    uvicorn.run(
        "robot_controller_web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
