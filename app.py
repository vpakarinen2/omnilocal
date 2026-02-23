import gradio as gr
import omni_engine


print("Initializing OmniLocal WebUI Pipeline...\n")
omni_engine.initialize()
print("Models Loaded Successfully!")


def chat_and_speak(user_input, chat_history, progress=gr.Progress()):
    progress(0.2, desc="Thinking...")
    
    messages = [{"role": "system", "content": omni_engine.SYSTEM_PROMPT}]
    for msg in chat_history or []:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_input})

    response_text = omni_engine.generate_text(messages)

    progress(0.8, desc="Generating Audio...")
    audio_path = omni_engine.generate_audio(response_text)

    chat_history.append({"role": "user", "content": user_input})
    chat_history.append({"role": "assistant", "content": response_text})
    
    return chat_history, "", audio_path


def vision_and_speak(image_path, prompt, progress=gr.Progress()):
    if not image_path:
        return "Please upload an image first.", None
        
    progress(0.2, desc="Analyzing Image...")
    try:
        response_text = omni_engine.generate_vision(image_path, prompt)
        progress(0.8, desc="Generating Audio...")
        audio_path = omni_engine.generate_audio(response_text)
        return response_text, audio_path
    except Exception as e:
        return f"Error processing image: {str(e)}", None


with gr.Blocks(title="OmniLocal", theme=gr.themes.Soft()) as demo:
    gr.Markdown("<center><h1>🌐 OmniLocal</h1></center>")
    gr.Markdown("<center><i>private voice-enabled assistant.</i></center>")
    
    with gr.Tabs():
        with gr.Tab("💬 Chat"):
            chatbot = gr.Chatbot(height=450, type="messages", label="Chat")
            with gr.Row():
                chat_txt = gr.Textbox(show_label=False, placeholder="Type your message here...", container=False, scale=8)
                chat_btn = gr.Button("Send", variant="primary", scale=1)
            chat_audio = gr.Audio(visible=True, autoplay=True, label="TTS")
            
            chat_txt.submit(chat_and_speak, inputs=[chat_txt, chatbot], outputs=[chatbot, chat_txt, chat_audio])
            chat_btn.click(chat_and_speak, inputs=[chat_txt, chatbot], outputs=[chatbot, chat_txt, chat_audio])
            
        with gr.Tab("👁️ Vision"):
            with gr.Row():
                with gr.Column(scale=1):
                    vis_image = gr.Image(type="filepath", label="Upload Image")
                    vis_prompt = gr.Textbox(label="Instructions", value="Describe this image in a natural, conversational way.")
                    vis_btn = gr.Button("Generate Caption", variant="primary")
                with gr.Column(scale=1):
                    vis_output = gr.Textbox(label="Generated Caption", lines=6, interactive=False)
                    vis_audio = gr.Audio(visible=True, autoplay=True, label="Caption TTS")
            
            vis_btn.click(vision_and_speak, inputs=[vis_image, vis_prompt], outputs=[vis_output, vis_audio])


if __name__ == "__main__":
    demo.launch(inbrowser=True)
