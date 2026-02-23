# 🌐 OmniLocal

**private voice-enabled multimodal assistant.**

OmniLocal is self-hosted WebUI and CLI that brings SOTA language, vision, and speech model to local hardware.

## 🖵 Screenshots
![OmniLocal Chat Tab](screenshots/chat_screenshot.png)
![OmniLocal Vision Tab](screenshots/vision_screenshot.png)

## ✨ Features

* **100% Local & Private:** Runs entirely on your GPU, No API keys or subscriptions
* **VRAM Hot-Swapping:** A built-in `ModelManager` hot-swaps models in and out of GPU memory
* **Text-to-Speech:** Realistic voice responses powered by the `Kokoro-82M` engine
* **Conversational AI:** Chat intelligently using SOTA `Phi-4-mini-instruct` model
* **Image Captioning:** Upload images and have them analyzed using `Qwen3-VL-2B-Instruct`
* **Dual Interfaces:** Sleek WebUI using Gradio and lightweight CLI with Python

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

## Author

Ville Pakarinen (@vpakarinen2)
