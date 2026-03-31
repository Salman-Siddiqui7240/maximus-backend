from fastapi import FastAPI, WebSocket
import os

# Initialize the cloud matrix
app = FastAPI(title="Maximus Cloud Core")

# 1. The Uptime Monitor Endpoint (To keep him awake 24/7)
@app.get("/")
def health_check():
    return {"status": "Maximus Cloud Matrix Online", "version": "1.0"}

# 2. The WebSocket Endpoint (Where your future mobile app will connect)
@app.websocket("/ws/command")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        query = data.get("query", "")
        # For now, he just echoes the command back to prove the connection works
        await websocket.send_json({"response": f"Cloud received your command: {query}", "status": "ok"})