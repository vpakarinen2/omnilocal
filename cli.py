import requests
import os


print("Initializing OmniLocal CLI Client...\n")

API_URL = "http://127.0.0.1:8000"
AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

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
        local_path = os.path.join(AUDIO_DIR, filename)
        response = requests.get(audio_url)
        with open(local_path, "wb") as f:
            f.write(response.content)
        return local_path
    except:
        return audio_url


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
        if not prompt: prompt = "Describe this image in a natural, conversational way."
            
        print("\nSending image to API...")
        try:
            res = requests.post(f"{API_URL}/api/vision", json={"image_path": image_path, "prompt": prompt})
            res.raise_for_status()
            data = res.json()
            
            print(f"OmniLocal: {data['response_text']}")
            saved_path = download_audio(data['audio_url'])
            print(f"(Audio saved to {saved_path})")
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
            
        except requests.exceptions.RequestException as e:
            print(f"[Connection Error] Make sure your FastAPI server is running. Details: {e}")
