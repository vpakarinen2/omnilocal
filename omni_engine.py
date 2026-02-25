import soundfile as sf
import torch
import os
import gc
import re

from transformers import AutoModelForCausalLM, AutoTokenizer, Qwen3VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from faster_whisper import WhisperModel
from datetime import datetime
from kokoro import KPipeline
from ddgs import DDGS


AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

MAX_NEW_TOKENS = 150
TEMPERATURE = 0.7
SYSTEM_PROMPT = "You are OmniLocal, a highly intelligent and concise conversational AI. Keep your answers brief, natural, and easy to read aloud. Do not use asterisks or markdown formatting."

tts_pipeline = None
stt_model = None
active_slot = None
llm_model = None
llm_tokenizer = None
vision_model = None
vision_processor = None


def initialize():
    global tts_pipeline, stt_model
    if tts_pipeline is None:
        print("[System] Loading TTS (Kokoro-82M)...")
        tts_pipeline = KPipeline(lang_code='a')
        
    if stt_model is None:
        print("[System] Loading STT (Faster-Whisper base)...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        stt_model = WhisperModel("medium", device=device, compute_type="float16")
        
    load_text_brain()


def load_text_brain():
    global active_slot, llm_model, llm_tokenizer, vision_model, vision_processor
    if active_slot == "text": return
        
    if vision_model is not None:
        print("\n[System] Unloading Vision Brain...")
        del vision_model, vision_processor
        vision_model, vision_processor = None, None
        gc.collect()
        torch.cuda.empty_cache()
        
    print("[System] Loading Text Brain (Phi-4-mini-instruct)...")
    llm_id = "microsoft/Phi-4-mini-instruct"
    llm_tokenizer = AutoTokenizer.from_pretrained(llm_id)
    llm_model = AutoModelForCausalLM.from_pretrained(llm_id, device_map="auto", torch_dtype=torch.float16)
    active_slot = "text"


def load_vision_brain():
    global active_slot, llm_model, llm_tokenizer, vision_model, vision_processor
    if active_slot == "vision": return
        
    if llm_model is not None:
        print("\n[System] Unloading Text Brain...")
        del llm_model, llm_tokenizer
        llm_model, llm_tokenizer = None, None
        gc.collect()
        torch.cuda.empty_cache()
        
    print("[System] Loading Vision Brain (Qwen3-VL-2B-Instruct)...")
    vision_id = "Qwen/Qwen3-VL-2B-Instruct"
    vision_processor = AutoProcessor.from_pretrained(vision_id)
    vision_model = Qwen3VLForConditionalGeneration.from_pretrained(vision_id, device_map="auto", torch_dtype=torch.float16)
    active_slot = "vision"


def search_web(query, max_results=5):
    print(f"\n[System] Searching the web for: '{query}'...")
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No web search results found."
            
        formatted_results = "CURRENT WEB CONTEXT:\n"
        for i, res in enumerate(results):
            formatted_results += f"{i+1}. {res['title']}: {res['body']}\n"
            
        return formatted_results
    except Exception as e:
        print(f"[Warning] Web search failed: {e}")
        return ""


def generate_text(messages, web_context=""):
    load_text_brain()
    
    if web_context:
        original_query = messages[-1]["content"]
        current_time = datetime.now().strftime("%A, %B %d, %Y %I:%M %p") # GET LIVE TIME
        
        forced_prompt = (
            f"Here is live web context I just searched for.\n"
            f"Current Date and Time: {current_time}\n"
            f"---------------------\n"
            f"{web_context}\n"
            f"---------------------\n"
            f"IGNORE your internal knowledge cutoff date. Do NOT say you cannot browse the internet or access real-time data. "
            f"Based EXCLUSIVELY on the live context above, answer the following question concisely: {original_query}"
        )
        messages[-1]["content"] = forced_prompt

    inputs = llm_tokenizer.apply_chat_template(
        messages, return_tensors="pt", add_generation_prompt=True, return_dict=True
    ).to(llm_model.device)
    
    with torch.no_grad():
        outputs = llm_model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=True, temperature=TEMPERATURE)
        
    generated_tokens = outputs[0][inputs['input_ids'].shape[1]:]
    return llm_tokenizer.decode(generated_tokens, skip_special_tokens=True)


def generate_vision(image_path, prompt):
    load_vision_brain()
    messages = [{"role": "user", "content": [{"type": "image", "image": f"file://{os.path.abspath(image_path)}"}, {"type": "text", "text": prompt}]}]
    
    text_prompt = vision_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    
    inputs = vision_processor(text=[text_prompt], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt").to(vision_model.device)
    
    with torch.no_grad():
        outputs = vision_model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS)
        
    generated_tokens = outputs[0][inputs['input_ids'].shape[1]:]
    return vision_processor.decode(generated_tokens, skip_special_tokens=True)


def generate_audio(text):
    clean_text = re.sub(r'[*_#`~]', '', text)
    generator = tts_pipeline(clean_text, voice='af_heart', speed=1)
    
    full_audio = []
    for _, _, audio_chunk in generator:
        full_audio.extend(audio_chunk)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(AUDIO_DIR, f"omnilocal_response_{timestamp}.wav")
    sf.write(output_filename, full_audio, 24000)
    return output_filename


def transcribe_audio(audio_path):
    print(f"\n[System] Transcribing audio from {audio_path}...")
    segments, info = stt_model.transcribe(audio_path, beam_size=5)
    text = "".join([segment.text for segment in segments])
    return text.strip()
