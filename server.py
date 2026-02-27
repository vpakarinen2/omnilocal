import shutil
import os

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import FileResponse
from typing import List, Optional
from pydantic import BaseModel

import omni_engine


app = FastAPI(title="OmniLocal API", version="1.0")

@app.on_event("startup")
async def startup_event():
    print("\n[System] Starting FastAPI Server...")
    omni_engine.initialize()
    print("[System] OmniLocal API is running and ready for requests!\n")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_input: str
    chat_history: Optional[List[ChatMessage]] = []
    use_search: bool = False

class OmniResponse(BaseModel):
    response_text: str
    audio_url: str
    
class TranscribeResponse(BaseModel):
    text: str

@app.post("/api/chat", response_model=OmniResponse)
def chat_endpoint(request: ChatRequest):
    try:
        web_context = ""
        if request.use_search:
            web_context = omni_engine.search_web(request.user_input)
            
        messages = [{"role": "system", "content": omni_engine.SYSTEM_PROMPT}]
        for msg in request.chat_history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": request.user_input})

        response_text = omni_engine.generate_text(messages, web_context)
        audio_path = omni_engine.generate_audio(response_text)
        
        audio_filename = os.path.basename(audio_path)
        audio_url = f"http://127.0.0.1:8000/audio/{audio_filename}"

        return OmniResponse(response_text=response_text, audio_url=audio_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vision", response_model=OmniResponse)
def vision_endpoint(prompt: str = Form(...), image_file: UploadFile = File(...)):
    temp_path = f"temp_vision_{image_file.filename}"
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)
            
        response_text = omni_engine.generate_vision(temp_path, prompt)
        audio_path = omni_engine.generate_audio(response_text)
        
        audio_filename = os.path.basename(audio_path)
        audio_url = f"http://127.0.0.1:8000/audio/{audio_filename}"

        return OmniResponse(response_text=response_text, audio_url=audio_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe_endpoint(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        transcribed_text = omni_engine.transcribe_audio(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return TranscribeResponse(text=transcribed_text)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{filename}")
async def get_audio(filename: str, background_tasks: BackgroundTasks):
    base_dir = os.path.abspath(omni_engine.AUDIO_DIR)
    file_path = os.path.abspath(os.path.join(base_dir, filename))
    
    if not file_path.startswith(base_dir):
        raise HTTPException(status_code=400, detail="Invalid file path.")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found.")
        
    background_tasks.add_task(os.remove, file_path)
    
    return FileResponse(file_path, media_type="audio/wav")
