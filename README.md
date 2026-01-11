# 🤖 L.U.D.O - Learning & Utility Digital Operator

<div align="center">

![LUDO Banner](HUD/jarvis.gif)

**An AI-Powered Voice Assistant with HUD Interface**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Pygame](https://img.shields.io/badge/Pygame-2.6.1-green.svg)](https://www.pygame.org/)
[![VITS TTS](https://img.shields.io/badge/TTS-VITS%20Neural-purple.svg)](https://github.com/rhasspy/piper)

</div>

---

## 🌟 Features

### 🎤 **Advanced Voice Assistant**
- **Google Gemini 2.0** AI integration for intelligent conversations
- **VITS Neural TTS** - Free, high-quality text-to-speech (Piper)
- **Speech Recognition** - Voice input support
- **Conversation Memory** - Remembers context across sessions
- **Smart Summarization** - Automatic conversation compression

### 🌐 **Internet Capabilities**
- **Web Search** - DuckDuckGo integration with result caching
- **Smart Triggers** - Intelligent search detection
- **Offline Mode** - Works without internet for basic functions

### 🎨 **Visual HUD Interface**
- **Animated LUDO Face** - Dynamic GIF display
- **Real-time Calendar** - Current date highlighting
- **Audio Visualization** - Waveform display
- **Project Tracking** - Multi-project management
- **To-Do List** - Task management
- **Notepad** - Quick note-taking

### 🖐️ **Hand Gesture Control**
- **MediaPipe Integration** - Hand tracking
- **Drag & Drop** - Move LUDO with hand gestures
- **Gesture Recognition** - Fist detection

### 🧠 **Memory Optimization**
- **Token Management** - ~50% reduction in API usage
- **Sliding Window** - Keep recent conversations in full detail
- **Auto-Summarization** - Compress older conversations
- **Context Budget** - 2000 token limit enforcement

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Windows OS** (tested on Windows 10/11)
- **Microphone** (for voice input)
- **Webcam** (optional, for hand tracking)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/AI_Miles.git
   cd AI_Miles
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   copy .env.example .env
   ```
   
   Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
   
   Get a free API key: [Google AI Studio](https://ai.google.dev/)

5. **Run LUDO**
   
   **Option A:** Desktop Application (Recommended)
   ```bash
   # Double-click Start_LUDO.bat
   ```
   
   **Option B:** Command Line
   ```bash
   python HUD\JarvisHUD.py
   ```

---

## 📖 Usage

### Voice Commands

- **Press Space** - Activate voice input
- **Type in chat box** - Text input mode
- **Ask questions** - LUDO responds with AI
- **"Note this: [text]"** - Save to notepad
- **Web searches** - Automatic when needed

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Start voice input |
| `F11` | Toggle fullscreen |
| `Esc` | Exit application |
| `Enter` | Send text input |

### Configuration

Edit `HUD/JarvisHUD.py` to customize:

```python
# Voice Settings
USE_VITS_TTS = True  # Neural voice (free)
VITS_VOICE_MODEL = "en_US-lessac-medium"  # Voice selection
VITS_SPEAKING_RATE = 1.05  # Speed

# Memory Settings
MAX_CONTEXT_TOKENS = 2000  # Token budget
ENABLE_AUTO_SUMMARIZATION = True  # Auto-compress old conversations

# Features
ENABLE_VOICE_ASSISTANT = True
ENABLE_HAND_TRACKING = True
```

---

## 🎯 Features in Detail

### 🗣️ VITS Neural TTS

LUDO uses **Piper** for free, offline, high-quality text-to-speech:

- ✅ **Free** - No API costs
- ✅ **Offline** - Works without internet
- ✅ **Natural** - Neural voice quality
- ✅ **Fast** - Real-time synthesis on CPU

**Available Voices:**
- `en_US-lessac-medium` - Male, clear (default)
- `en_US-amy-medium` - Female, warm
- `en_US-ryan-high` - Male, young

### 🧠 Memory Optimization

Smart conversation management:

- **Token Counting** - Tracks API usage
- **Sliding Window** - Keeps 10 recent messages
- **Auto-Summarization** - Compresses older context
- **50% Token Reduction** - Saves API costs

### 🌐 Web Search

Intelligent web integration:

- **DuckDuckGo** - Privacy-focused search
- **Result Caching** - Avoid duplicate searches
- **Smart Triggers** - Only search when needed
- **Snippet Extraction** - Concise results

---

## 📁 Project Structure

```
AI_Miles/
├── HUD/
│   ├── JarvisHUD.py          # Main application
│   ├── token_counter.py      # Memory optimization
│   ├── vits_tts.py           # Neural TTS engine
│   ├── jarvis.gif            # LUDO face animation
│   ├── *.png                 # UI assets
│   └── Orbitron-*.ttf        # Custom font
├── .venv/                    # Virtual environment
├── Start_LUDO.bat            # Desktop launcher
├── Start_LUDO_Silent.bat     # Silent launcher
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## 🔧 Advanced Configuration

### Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_api_key_here
AZURE_SPEECH_KEY=optional_azure_key
AZURE_SPEECH_REGION=eastus
```

### Custom Voice Models

Download additional Piper voices:
- [Voice Gallery](https://rhasspy.github.io/piper-samples/)
- [Model Downloads](https://huggingface.co/rhasspy/piper-voices)

### Desktop Integration

**Create desktop shortcut:**
```powershell
powershell -ExecutionPolicy Bypass -File Create_Desktop_Shortcut.ps1
```

**Auto-start on login:**
1. Press `Win + R`
2. Type `shell:startup`
3. Copy `LUDO.lnk` shortcut there

---

## 🛠️ Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
pip install -r requirements.txt
```

**"GEMINI_API_KEY not found"**
- Create `.env` file from `.env.example`
- Add your API key

**Audio playback issues**
```bash
pip install pyaudio --upgrade
```

**Hand tracking not working**
```bash
pip install mediapipe --upgrade
```

### Performance Tips

- **Disable hand tracking** if not needed (saves CPU)
- **Use silent launcher** for background mode
- **Adjust token budget** for faster responses

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| **Token Reduction** | ~50% |
| **Response Time** | <2s |
| **Memory Usage** | ~100MB |
| **TTS Latency** | <1s |
| **Search Cache Hit** | ~60% |

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini** - AI conversation engine
- **Piper TTS** - Neural voice synthesis
- **Pygame** - Graphics and UI
- **MediaPipe** - Hand tracking
- **DuckDuckGo** - Web search

---

## 📧 Contact

**Project Maintainer:** Sathyaseelan 
**Email:** ksathyaseelan34@gmail.com
**GitHub:** [Sathyaseelan](https://github.com/sathyaseelan2006)

---

<div align="center">


⭐ Star this repo if you find it useful!

</div>
