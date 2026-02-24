import os

from fastapi import FastAPI, HTTPException
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

class VisionRequest(BaseModel):
    image_path: str
    prompt: str

class OmniResponse(BaseModel):
    response_text: str
    audio_url: str


@app.post("/api/chat", response_model=OmniResponse)
async def chat_endpoint(request: ChatRequest):
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
async def vision_endpoint(request: VisionRequest):
    if not os.path.exists(request.image_path):
        raise HTTPException(status_code=400, detail="Image file not found on server.")
        
    try:
        response_text = omni_engine.generate_vision(request.image_path, request.prompt)
        audio_path = omni_engine.generate_audio(response_text)
        
        audio_filename = os.path.basename(audio_path)
        audio_url = f"http://127.0.0.1:8000/audio/{audio_filename}"

        return OmniResponse(response_text=response_text, audio_url=audio_url)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serves the generated .wav files directly to the browser/client."""
    file_path = os.path.join(omni_engine.AUDIO_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found.")
    
    return FileResponse(file_path, media_type="audio/wav")
