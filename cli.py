import os
import omni_engine


print("Initializing OmniLocal CLI...\n")
omni_engine.initialize()

print("\n" + "="*25)
print("OmniLocal (CLI)")
print("- Type normally to chat.")
print("- Type '/search [query]' to make a web search query.")
print("- Type '/image [path/to/image.jpg]' to analyze an image.")
print("- Type 'exit' to quit.")
print("="*25)

chat_history = [{"role": "system", "content": omni_engine.SYSTEM_PROMPT}]


while True:
    user_input = input("\nUser: ").strip()
    if user_input.lower() in ['exit', 'quit']:
        print("Goodbye!")
        break
    if not user_input:
        continue

    web_context = ""

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
            
        print("\nLooking at the image...")
        try:
            response_text = omni_engine.generate_vision(image_path, prompt)
        except Exception as e:
            print(f"[Error] Failed to process image: {e}")
            continue

    elif user_input.startswith("/search "):
        query = user_input[8:].strip()
        web_context = omni_engine.search_web(query)
        print("\nThinking...")
        
        chat_history.append({"role": "user", "content": query})
        messages = [{"role": "system", "content": omni_engine.SYSTEM_PROMPT}] + chat_history[1:]
        response_text = omni_engine.generate_text(messages, web_context)
        chat_history.append({"role": "assistant", "content": response_text})

    else:
        print("\nThinking...")
        chat_history.append({"role": "user", "content": user_input})
        
        messages = [{"role": "system", "content": omni_engine.SYSTEM_PROMPT}] + chat_history[1:]
        response_text = omni_engine.generate_text(messages)
        chat_history.append({"role": "assistant", "content": response_text})

    print(f"OmniLocal: {response_text}")
    print("(Generating Audio...)")
    audio_path = omni_engine.generate_audio(response_text)
    print(f"(Audio saved to {audio_path})")
