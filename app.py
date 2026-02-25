import gradio as gr
import requests
import os


print("Initializing OmniLocal WebUI Client...\n")

API_URL = "http://127.0.0.1:8000"
CLIENT_AUDIO_DIR = "client_audio"
os.makedirs(CLIENT_AUDIO_DIR, exist_ok=True)


def download_audio(audio_url):
    try:
        filename = audio_url.split("/")[-1]
        local_path = os.path.join(CLIENT_AUDIO_DIR, filename)
        response = requests.get(audio_url)
        with open(local_path, "wb") as f:
            f.write(response.content)
        return local_path
    except Exception as e:
        print(f"Failed to download audio: {e}")
        return None


def chat_and_speak(user_input, chat_history, use_search, progress=gr.Progress()):
    if not user_input.strip():
        return chat_history, "", None
        
    progress(0.2, desc="Sending request to server...")
    
    formatted_history = []
    if chat_history:
        for msg in chat_history:
            formatted_history.append({"role": msg["role"], "content": msg["content"]})
            
    payload = {
        "user_input": user_input,
        "chat_history": formatted_history,
        "use_search": use_search
    }
    
    try:
        progress(0.5, desc="Waiting for OmniLocal API...")
        response = requests.post(f"{API_URL}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        
        response_text = data["response_text"]
        
        progress(0.8, desc="Downloading Audio...")
        local_audio_path = download_audio(data["audio_url"])
        
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": response_text})
        
        return chat_history, "", local_audio_path
        
    except requests.exceptions.RequestException as e:
        error_msg = f"[Connection Error] Is the FastAPI server running? Details: {e}"
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": error_msg})
        return chat_history, "", None


def transcribe_and_chat(audio_path, chat_history, use_search, progress=gr.Progress()):
    if not audio_path:
        return chat_history, "", None, None
        
    progress(0.1, desc="🎙️ Transcribing...")
    try:
        with open(audio_path, "rb") as f:
            res = requests.post(f"{API_URL}/api/transcribe", files={"file": f})
        res.raise_for_status()
        user_text = res.json().get("text", "").strip()
        
    except Exception as e:
        print(f"Transcription error: {e}")
        error_msg = "[Transcription Error] Could not understand audio or server is down."
        chat_history.append({"role": "user", "content": "🎤 (Voice Message)"})
        chat_history.append({"role": "assistant", "content": error_msg})
        return chat_history, "", None, None

    if not user_text:
        return chat_history, "", None, None
        
    history, txt, audio = chat_and_speak(user_text, chat_history, use_search, progress)
    
    return history, txt, audio, None


def vision_and_speak(image_path, prompt, progress=gr.Progress()):
    if not image_path:
        return "Please upload an image first.", None
        
    progress(0.2, desc="Sending image to server...")
    payload = {
        "image_path": image_path,
        "prompt": prompt
    }
    
    try:
        progress(0.5, desc="Waiting for Vision API...")
        response = requests.post(f"{API_URL}/api/vision", json=payload)
        response.raise_for_status()
        data = response.json()
        
        progress(0.8, desc="Downloading Audio...")
        local_audio_path = download_audio(data["audio_url"])
        
        return data["response_text"], local_audio_path
        
    except requests.exceptions.RequestException as e:
        return f"[Connection Error] Is the FastAPI server running? Details: {e}", None


with gr.Blocks(title="OmniLocal", theme=gr.themes.Soft()) as demo:
    gr.Markdown("<center><h1>🌐 OmniLocal</h1></center>")
    gr.Markdown("<center><i>private voice-enabled assistant.</i></center>")
    
    with gr.Tabs():
        with gr.Tab("💬 Chat"):
            chatbot = gr.Chatbot(height=450, type="messages", label="Chat", allow_tags=True)
            
            with gr.Row():
                with gr.Column(scale=5):
                    mic_input = gr.Audio(sources=["microphone"], type="filepath", label="Voice")
                    chat_txt = gr.Textbox(show_label=False, placeholder="Type your message here...")
                    
                with gr.Column(scale=1):
                    web_search_toggle = gr.Checkbox(label="🌐 Search Web")
                    chat_btn = gr.Button("Send", variant="primary", size="lg")
                
            chat_audio = gr.Audio(visible=True, autoplay=True, label="Chat TTS")
            
            mic_input.stop_recording(transcribe_and_chat, inputs=[mic_input, chatbot, web_search_toggle], outputs=[chatbot, chat_txt, chat_audio, mic_input])
            mic_input.upload(transcribe_and_chat, inputs=[mic_input, chatbot, web_search_toggle], outputs=[chatbot, chat_txt, chat_audio, mic_input])
            
            chat_txt.submit(chat_and_speak, inputs=[chat_txt, chatbot, web_search_toggle], outputs=[chatbot, chat_txt, chat_audio])
            chat_btn.click(chat_and_speak, inputs=[chat_txt, chatbot, web_search_toggle], outputs=[chatbot, chat_txt, chat_audio])
            
        with gr.Tab("👁️ Vision"):
            with gr.Row():
                with gr.Column(scale=1):
                    vis_image = gr.Image(type="filepath", label="Upload Image")
                    vis_prompt = gr.Textbox(label="Instructions", value="Describe this image in three sentences.")
                    vis_btn = gr.Button("Generate Caption", variant="primary")
                with gr.Column(scale=1):
                    vis_output = gr.Textbox(label="Generated Caption", lines=6, interactive=False)
                    vis_audio = gr.Audio(visible=True, autoplay=True, label="Caption TTS")
            
            vis_btn.click(vision_and_speak, inputs=[vis_image, vis_prompt], outputs=[vis_output, vis_audio])


if __name__ == "__main__":
    demo.launch(inbrowser=True)
