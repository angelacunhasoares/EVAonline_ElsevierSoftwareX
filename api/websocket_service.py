from fastapi import FastAPI, WebSocket
from celery.result import AsyncResult
import json
import asyncio

app = FastAPI()


@app.websocket("/ws/task_status")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        task_id = await websocket.receive_text()
        task = AsyncResult(task_id)
        while not task.ready():
            await websocket.send_json({"status": task.state, "info": task.info or {}})
            await asyncio.sleep(1)
        task_result = task.get()
        if task_result is None:
            result, warnings = None, None
        else:
            result, warnings = task_result
        await websocket.send_json({"status": "SUCCESS", "result": result.to_dict() if result else None, "warnings": warnings})
    except Exception as e:
        await websocket.send_json({"status": "ERROR", "error": str(e)})
    finally:
        await websocket.close()