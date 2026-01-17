"""
VITS-based TTS using Piper
Free, fast, high-quality neural voices for LUDO
"""

import os
import tempfile
import wave
import pyaudio
from piper import PiperVoice

class VITSTTSEngine:
    """VITS-based Text-to-Speech engine using Piper"""
    
    def __init__(self, model_name="en_US-lessac-medium"):
        """
        Initialize VITS TTS engine
        
        Args:
            model_name: Piper voice model name
                       Popular options:
                       - en_US-lessac-medium (male, clear)
                       - en_US-amy-medium (female, warm)
                       - en_US-ryan-high (male, young)
        """
        self.model_name = model_name
        self.voice = None
        self.initialized = False
        
    def initialize(self):
        """Initialize Piper voice model (auto-downloads on first use)"""
        try:
            print(f"🔄 Loading VITS voice model: {self.model_name}...")
            
            # Check if model files exist in common locations
            model_paths = [
                f"{self.model_name}.onnx",
                f"models/{self.model_name}.onnx",
                os.path.expanduser(f"~/.local/share/piper-tts/voices/{self.model_name}.onnx")
            ]
            
            # Try to load the voice
            self.voice = PiperVoice.load(self.model_name)
            self.initialized = True
            print(f"✅ VITS TTS initialized with {self.model_name}")
            return True
        except FileNotFoundError as e:
            print(f"⚠️ VITS model not found: {self.model_name}")
            print(f"💡 To use VITS TTS, download the model from:")
            print(f"   https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/lessac/medium")
            print(f"   Place .onnx and .json files in the HUD directory")
            print(f"🔄 Falling back to basic TTS...")
            return False
        except Exception as e:
            print(f"❌ VITS TTS initialization failed: {e}")
            print(f"🔄 Falling back to basic TTS...")
            return False
    
    def speak(self, text, rate=1.0):
        """
        Convert text to speech and play it
        
        Args:
            text: Text to speak
            rate: Speaking rate (0.5-2.0, default 1.0)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.initialized:
            if not self.initialize():
                return False
        
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_file = f.name
            
            # Synthesize speech with Piper
            # length_scale controls speed (inverse of rate)
            with wave.open(temp_file, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(22050)  # Piper default sample rate
                
                # Synthesize audio
                audio_bytes = self.voice.synthesize(text, length_scale=1.0/rate)
                wav_file.writeframes(audio_bytes)
            
            # Play audio using PyAudio
            self._play_wav(temp_file)
            
            # Cleanup
            try:
                os.unlink(temp_file)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ VITS TTS error: {e}")
            return False
    
    def _play_wav(self, wav_file):
        """Play WAV file using PyAudio"""
        try:
            # Open WAV file
            wf = wave.open(wav_file, 'rb')
            
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            # Open stream
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            # Play audio
            chunk = 1024
            data = wf.readframes(chunk)
            while data:
                stream.write(data)
                data = wf.readframes(chunk)
            
            # Cleanup
            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()
            
        except Exception as e:
            print(f"⚠️ Audio playback error: {e}")


# Test the engine
if __name__ == "__main__":
    print("Testing VITS TTS Engine...")
    engine = VITSTTSEngine()
    
    test_text = "Hello! I am LUDO, your AI assistant. This is my new VITS neural voice."
    print(f"Speaking: {test_text}")
    
    if engine.speak(test_text):
        print("✅ VITS TTS test successful!")
    else:
        print("❌ VITS TTS test failed")
