import subprocess
import platform
import requests
import os


print("Initializing OmniLocal CLI Client...\n")

API_URL = os.getenv("OMNI_API_URL", "http://127.0.0.1:8000")
CLIENT_AUDIO_DIR = "client_audio" 
os.makedirs(CLIENT_AUDIO_DIR, exist_ok=True)

print("="*25)
print("OmniLocal (CLI)")
print("- Type normally to chat.")
print("- Type '/search [query]' to make a web search.")
print("- Type '/image [path/to/image.jpg]' to analyze an image.")
print("- Type 'exit' to quit.")
print("="*25)

chat_history = []


def download_audio(audio_url):
    """Helper to download the audio file from the server."""
    try:
        filename = audio_url.split("/")[-1]
        local_path = os.path.join(CLIENT_AUDIO_DIR, filename) 
        response = requests.get(audio_url)

        response.raise_for_status() 
        
        with open(local_path, "wb") as f:
            f.write(response.content)
        return local_path
    except Exception as e:
        print(f"  [Warning] Could not download audio: {e}") 
        return audio_url


def play_audio(file_path):
    try:
        if platform.system() == "Darwin":       
            subprocess.run(["afplay", file_path])
        elif platform.system() == "Linux":      
            subprocess.run(["aplay", file_path])
        elif platform.system() == "Windows":    
            os.startfile(file_path)
    except Exception as e:
        print(f"[Audio Error] Could not play audio: {e}")


while True:
    user_input = input("\nUser: ").strip()
    if user_input.lower() in ['exit', 'quit']:
        print("Goodbye!")
        break
    if not user_input:
        continue

    if user_input.startswith("/image"):
        parts = user_input.split(" ", 1)
        if len(parts) < 2:
            print("[Error] Please provide an image path.")
            continue
            
        image_path = parts[1].strip().strip("\"'") 
        if not os.path.exists(image_path):
            print(f"[Error] Could not find file: {image_path}")
            continue
            
        prompt = input("Image Prompt (Press Enter for 'Describe this image'): ").strip()
        if not prompt: prompt = "Describe this image in three sentences."
            
        print("\nSending image to API...")
        try:
            with open(image_path, "rb") as image_file:
                res = requests.post(
                    f"{API_URL}/api/vision", 
                    data={"prompt": prompt},
                    files={"image_file": image_file}
                )
            res.raise_for_status()
            data = res.json()
            
            print(f"OmniLocal: {data['response_text']}")
            saved_path = download_audio(data['audio_url'])
            print(f"(Audio saved to {saved_path})")
            
            if os.path.exists(saved_path):
                play_audio(saved_path)
                
        except requests.exceptions.RequestException as e:
            print(f"[Connection Error] Make sure your FastAPI server is running. Details: {e}")

    else:
        use_search = False
        query = user_input
        
        if user_input.startswith("/search "):
            use_search = True
            query = user_input[8:].strip()
            
        print("\nSending request to API...")
        payload = {
            "user_input": query,
            "chat_history": chat_history,
            "use_search": use_search
        }
        
        try:
            res = requests.post(f"{API_URL}/api/chat", json=payload)
            res.raise_for_status()
            data = res.json()
            
            response_text = data["response_text"]
            
            chat_history.append({"role": "user", "content": query})
            chat_history.append({"role": "assistant", "content": response_text})
            
            print(f"OmniLocal: {response_text}")
            saved_path = download_audio(data['audio_url'])
            print(f"(Audio saved to {saved_path})")
            
            if os.path.exists(saved_path):
                play_audio(saved_path)
            
        except requests.exceptions.RequestException as e:
            print(f"[Connection Error] Make sure your FastAPI server is running. Details: {e}")
