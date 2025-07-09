from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import asyncio
from assistant import AudioOnlyLoop

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

assistant_instance = AudioOnlyLoop()
assistant_task = None
transcription_queue = asyncio.Queue()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/start")
async def start_assistant():
    global assistant_task
    if assistant_task is None or assistant_task.done():
        assistant_task = asyncio.create_task(assistant_instance.run(transcription_queue))
        return {"status": "started"}
    return {"status": "already running"}


@app.post("/stop")
async def stop_assistant():
    global assistant_task
    if assistant_task:
        assistant_task.cancel()
        return {"status": "stopped"}
    return {"status": "not running"}


@app.websocket("/ws/transcription")
async def transcription_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            text = await transcription_queue.get()
            await websocket.send_text(text)
    except Exception:
        await websocket.close()
