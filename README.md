# 🌐 OmniLocal

**fully local and private multi-modal assistant.**

OmniLocal is a self-hosted WebUI and CLI that brings state-of-the-art language, vision, and speech models directly to your local hardware. It processes text and images, and natively speaks responses using text-to-speech.

## ✨ Features

* **100% Local & Private:** Runs entirely on your GPU, No API keys or subscriptions
* **VRAM Hot-Swapping:** A built-in `ModelManager` hot-swaps models in and out of GPU memory
* **Text-to-Speech:** Realistic voice responses powered by the `Kokoro-82M` engine
* **Conversational AI:** Chat intelligently using SOTA `Phi-4-mini-instruct` model
* **Image Captioning:** Upload images and have them analyzed using `Qwen3-VL-2B-Instruct`
* **Dual Interface:** Sleek WebUI using Gradio and fast lightweight CLI with Python

## 🛠️ Installation

### 1. Prerequisites
* **Nvidia GPU** (At least 6GB+ VRAM recommended)
* **Python 3.11+** installed on your system
* **PyTorch** with CUDA 12.1

### 2. Setup Environment
```
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Mac/Linux
```

### 3. Install PyTorch (CUDA)
```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```
### 4. Install Requirements
```
pip install -r requirements.txt
pip install qwen-vl-utils
```

## 🚀 Usage

### WebUI
```
python app.py
```

### CLI
```
python cli.py
```
