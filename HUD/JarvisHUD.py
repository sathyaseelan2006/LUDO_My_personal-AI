import pygame
import pyaudio
import struct
from PIL import Image, ImageSequence
import datetime
import calendar as cal_module
import threading
import os
import cv2
import mediapipe as mp
import numpy as np
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import json
import requests
from bs4 import BeautifulSoup
import urllib.parse
from token_counter import estimate_tokens, estimate_conversation_tokens, trim_to_token_budget, create_conversation_summary, get_context_stats
from vits_tts import VITSTTSEngine

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")

# Adapted for Windows
# Uses Python 3.10.9 or higher

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')  # Load from environment variable
if not GEMINI_API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in environment variables!")
    print("Please create a .env file or set the GEMINI_API_KEY environment variable.")
    print("See .env.example for template.")

try:
    # Configure Gemini API
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_enabled = True
    else:
        gemini_enabled = False
        print("❌ Gemini API disabled - no API key provided")
except Exception as e:
    print(f"Gemini initialization failed: {e}")
    gemini_enabled = False

# Voice Assistant Configuration
ENABLE_VOICE_ASSISTANT = True  # Set to True or False
ENABLE_HAND_TRACKING = True  # Set to True or False for hand control

# === VITS Neural Voice Configuration (FREE) ===
USE_VITS_TTS = True  # Use VITS neural voices (Piper)
VITS_VOICE_MODEL = "en_US-lessac-medium"  # Voice: lessac (male), amy (female), ryan (male-young)
VITS_SPEAKING_RATE = 1.05  # Speed multiplier (0.5-2.0)

# === PHASE 2: Azure Neural Voice Configuration ===
# Uncomment and configure when ready to upgrade
USE_AZURE_TTS = False  # Set to True to use Azure Neural Voices
AZURE_SPEECH_KEY = ""  # Your Azure Speech Services API key
AZURE_SPEECH_REGION = "eastus"  # Your Azure region (e.g., eastus, westus, etc.)
AZURE_VOICE_NAME = "en-US-GuyNeural"  # Azure Neural Voice (Guy, Aria, Davis, Jane, Jason, Jenny, Nancy, Sara, Tony)
AZURE_VOICE_STYLE = "friendly"  # Speaking style: chat, cheerful, empathetic, excited, friendly, hopeful, sad, etc.
AZURE_SPEAKING_RATE = 1.05  # 0.5 to 2.0 (1.0 = normal)
AZURE_PITCH = "+0Hz"  # Pitch adjustment: -50Hz to +50Hz or relative like "+10%"

# Voice Settings (Customize LUDO's voice here!)
VOICE_INDEX = 1      # Voice selection: 0 (Microsoft David - smooth male voice)
VOICE_RATE = 165        # Speech speed: 165 for younger, smoother sound
VOICE_VOLUME = 0.85     # Volume: 0.85 for softer, more soothing tone

# Conversation Memory Settings
MAX_CONVERSATION_HISTORY = 20  # Keep last N messages (user + assistant pairs)
MAX_CONTEXT_TOKENS = 2000  # Maximum tokens for context window
RECENT_CONVERSATION_COUNT = 10  # Keep last N messages in full detail (5 exchanges)
ENABLE_AUTO_SUMMARIZATION = True  # Automatically summarize old conversations
MEMORY_FILE = r"E:\brainstroming\AI_Miles\HUD\.ludo_memory.json"  # Persistent memory file
CONTEXT_FILE = r"E:\brainstroming\AI_Miles\HUD\.ludo_context.json"  # Project context file
PROJECTS_FILE = r"E:\brainstroming\AI_Miles\HUD\.ludo_projects.json"  # Project tracking file

# Voice assistant globals
user_query = ""
assistant_response = ""
listening = False
processing = False
conversation_history = []  # Stores conversation memory
conversation_summary = ""  # Condensed summary of old conversations
text_input = ""  # Text input buffer
input_active = False  # Whether text input is active
search_cache = {}  # Cache for web search results (query -> results)

# VITS TTS engine
vits_engine = None
if USE_VITS_TTS:
    try:
        vits_engine = VITSTTSEngine(VITS_VOICE_MODEL)
        print(f"🎤 VITS TTS configured with {VITS_VOICE_MODEL}")
    except Exception as e:
        print(f"⚠️ VITS TTS initialization deferred: {e}")

# Notepad globals
notepad_entries = []  # List of notepad entries
NOTEPAD_FILE = r"E:\brainstroming\AI_Miles\HUD\.ludo_notepad.json"  # Persistent notepad file
MAX_NOTEPAD_ENTRIES = 50  # Maximum number of entries to keep

# Project context globals
current_context = {
    "project": "None",
    "repo": "None", 
    "topic": "None",
    "dataset": "None"
}
projects_data = {}  # Tracks project activity and deadlines


hand_landmarks_global = None
hand_closed_global = False
wrist_screen_pos = (0, 0)
ludo_x = None
ludo_y = None
grab_active = False


# Initialize pygame
pygame.init()

# Load custom font (Orbitron)
font_path = r'E:\brainstroming\AI_Miles\HUD\Orbitron-VariableFont_wght.ttf'
clock_font = pygame.font.Font(font_path, 80)
calendar_font = pygame.font.Font(font_path, 20)
description_font = pygame.font.Font(None, 18)  # Use default pygame font for proper case
chat_font = pygame.font.Font(None, 18)  # Separate font for chat messages

track_font = pygame.font.SysFont("SF Mono", 18)



CYAN = (0, 255, 255)
BLACK = (0, 0, 0)
HIGHLIGHT_ALPHA = 80

todo_file_path = r"E:\brainstroming\AI_Miles\HUD\.todo.txt" # Make a file called .todo.txt in the same directory as this script and write your to do list inside
todo_font = pygame.font.Font(font_path, 30)

def load_todo_tasks():
    if os.path.exists(todo_file_path):
        with open(todo_file_path, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

# Screen setup
info = pygame.display.Info()
screen_width, screen_height = info.current_w, info.current_h
screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
pygame.display.set_caption('L.U.D.O')

# Load LUDO face GIF
gif_path = r'E:\brainstroming\AI_Miles\HUD\jarvis.gif'
gif = Image.open(gif_path)
frames = [frame.copy().convert("RGBA") for frame in ImageSequence.Iterator(gif)]
frame_surfaces = [pygame.image.frombuffer(frame.tobytes(), frame.size, "RGBA") for frame in frames]

# Load Discord Icon
discord_icon_path = r'E:\brainstroming\AI_Miles\HUD\discord.png'
discord_icon_raw = pygame.image.load(discord_icon_path).convert_alpha()
discord_icon = pygame.transform.scale(discord_icon_raw, (0, 0))  # Optional: resize if needed

# Discord Icon position offset from bottom-left
discord_offset_x = 1150   # distance from left edge
discord_offset_y = 50   # distance from bottom edge

discord_pos_x = discord_offset_x
discord_pos_y = screen.get_height() - discord_icon.get_height() - discord_offset_y




# PyAudio setup
try:
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=512)
    audio_enabled = True
except Exception as e:
    print(f"Audio initialization failed: {e}. Running without audio visualization.")
    audio_enabled = False
    p = None
    stream = None

def get_volume(data):
    count = len(data) // 2
    format = "%dh" % count
    shorts = struct.unpack(format, data)
    sum_squares = sum(s**2 for s in shorts)
    return (sum_squares / count)**0.5

def get_calendar_data():
    try:
        now = datetime.datetime.now()
        month_cal = cal_module.month(now.year, now.month)
        lines = month_cal.strip().split('\n')
        return lines
    except Exception as e:
        print(f"Calendar fetch error: {e}")
        return []



def wrap_text(text, font, max_width):
    """Wrap text to fit within a maximum width"""
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        test_surface = font.render(test_line, True, (255, 255, 255))
        
        if test_surface.get_width() <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # Word is too long, split it
                lines.append(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def render_calendar(surface, x, y):
    lines = get_calendar_data()
    if not lines:
        return

    today = datetime.datetime.now().day
    weekdays = lines[1].split()
    cell_width = 35
    margin_left = 10
    cell_height = calendar_font.get_height() + 6

    header_surface = calendar_font.render(lines[0], True, CYAN)
    surface.blit(header_surface, (x, y))
    y_offset = y + header_surface.get_height() + 10

    cur_x = x
    for idx, day in enumerate(weekdays):
        day_surface = calendar_font.render(day, True, CYAN)
        if idx > 0:
            cur_x += margin_left
        surface.blit(day_surface, (cur_x, y_offset))
        cur_x += cell_width

    y_offset += cell_height + 10

    for week_line in lines[2:]:
        cur_x = x
        for i in range(7):
            start = i * 3
            day_str = week_line[start:start+3].strip()
            if day_str == '':
                day_str = ' '

            if i > 0:
                cur_x += margin_left

            if day_str.isdigit() and int(day_str) == today:
                highlight_surf = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
                pygame.draw.ellipse(highlight_surf, CYAN + (HIGHLIGHT_ALPHA,), highlight_surf.get_rect())
                surface.blit(highlight_surf, (cur_x, y_offset))
                day_surface = calendar_font.render(day_str, True, BLACK)
            else:
                day_surface = calendar_font.render(day_str, True, CYAN)

            day_rect = day_surface.get_rect()
            day_pos_x = cur_x + (cell_width - day_rect.width) // 2
            day_pos_y = y_offset + (cell_height - day_rect.height) // 2
            surface.blit(day_surface, (day_pos_x, day_pos_y))

            cur_x += cell_width

        y_offset += cell_height + 6

def toggle_fullscreen(screen, fullscreen):
    if fullscreen:
        pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    else:
        pygame.display.set_mode((800, 600))
    return not fullscreen

track = ""
track_lock = threading.Lock()

# Spotify track fetching removed - macOS specific feature
# For Windows, consider using Spotify API or spotipy library
def fetch_track():
    global track
    with track_lock:
        track = ""  # Disabled on Windows

# Memory Management Functions
def save_conversation_memory():
    """Save conversation history to file"""
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to save memory: {e}")

def load_conversation_memory():
    """Load conversation history from file"""
    global conversation_history
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                conversation_history = json.load(f)
            print(f"💾 Loaded {len(conversation_history)//2} previous conversation(s) from memory")
        else:
            print("💾 Starting with fresh memory")
    except Exception as e:
        print(f"Failed to load memory: {e}")
        conversation_history = []

# Context & Project Management Functions
def save_context():
    """Save current project context"""
    try:
        with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_context, f, indent=2)
    except Exception as e:
        print(f"Failed to save context: {e}")

def load_context():
    """Load project context"""
    global current_context
    try:
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
                current_context = json.load(f)
            print(f"📁 Context loaded: {current_context['project']}")
    except Exception as e:
        print(f"Failed to load context: {e}")

def save_projects():
    """Save project tracking data"""
    try:
        with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(projects_data, f, indent=2)
    except Exception as e:
        print(f"Failed to save projects: {e}")

def load_projects():
    """Load project tracking data"""
    global projects_data
    try:
        if os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
                projects_data = json.load(f)
            print(f"📊 Loaded {len(projects_data)} tracked project(s)")
    except Exception as e:
        print(f"Failed to load projects: {e}")

# Notepad Management Functions
def save_notepad():
    """Save notepad entries to file"""
    try:
        with open(NOTEPAD_FILE, 'w', encoding='utf-8') as f:
            json.dump(notepad_entries, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to save notepad: {e}")

def load_notepad():
    """Load notepad entries from file"""
    global notepad_entries
    try:
        if os.path.exists(NOTEPAD_FILE):
            with open(NOTEPAD_FILE, 'r', encoding='utf-8') as f:
                notepad_entries = json.load(f)
            print(f"📝 Loaded {len(notepad_entries)} notepad entries")
        else:
            print("📝 Starting with empty notepad")
    except Exception as e:
        print(f"Failed to load notepad: {e}")
        notepad_entries = []

def add_notepad_entry(text):
    """Add a new entry to the notepad"""
    global notepad_entries
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "text": text
    }
    notepad_entries.insert(0, entry)  # Add to beginning
    
    # Keep only max entries
    if len(notepad_entries) > MAX_NOTEPAD_ENTRIES:
        notepad_entries = notepad_entries[:MAX_NOTEPAD_ENTRIES]
    
    save_notepad()
    print(f"📝 Note added: {text}")

def check_notepad_command(query):
    """Check if query is a notepad command and extract the note"""
    query_lower = query.lower().strip()
    
    # Notepad trigger phrases - more comprehensive list
    notepad_triggers = [
        ('note this:', ':'),
        ('note that:', ':'),
        ('note:', ':'),
        ('idea:', ':'),
        ('quote:', ':'),
        ('thought:', ':'),
        ('reminder:', ':'),
        ('make a note', None),
        ('add note', None),
        ('add to notes', None),
        ('write this down', None),
        ('remember this', None),
        ('save this note', None),
        ('add to notepad', None),
        ('jot this down', None),
        ('quick note', None),
    ]
    
    # Check each trigger
    for trigger_info in notepad_triggers:
        if isinstance(trigger_info, tuple):
            trigger, separator = trigger_info
        else:
            trigger = trigger_info
            separator = None
        
        if trigger in query_lower:
            # Extract the note content
            if separator and separator in query:
                # Split by the separator and take everything after
                parts = query.split(separator, 1)
                if len(parts) > 1:
                    note_text = parts[1].strip()
                    if note_text:
                        return note_text
            else:
                # Remove the trigger phrase and get the rest
                trigger_idx = query_lower.find(trigger)
                start_idx = trigger_idx + len(trigger)
                note_text = query[start_idx:].strip()
                
                # Remove common connecting words at the start
                for word in ['that ', 'this ', '- ', ': ']:
                    if note_text.lower().startswith(word):
                        note_text = note_text[len(word):].strip()
                
                if note_text:
                    return note_text
    
    return None

def update_project_activity(project_name):
    """Update last activity timestamp for a project"""
    projects_data[project_name] = {
        "last_activity": datetime.datetime.now().isoformat(),
        "deadline": projects_data.get(project_name, {}).get("deadline", "")
    }
    save_projects()

def get_project_reminders():
    """Get reminders about project activity"""
    reminders = []
    now = datetime.datetime.now()
    
    for project, data in projects_data.items():
        if "last_activity" in data:
            last = datetime.datetime.fromisoformat(data["last_activity"])
            days_ago = (now - last).days
            if days_ago > 0:
                reminders.append(f"{project}: {days_ago} days ago")
        
        if "deadline" in data and data["deadline"]:
            try:
                deadline = datetime.datetime.fromisoformat(data["deadline"])
                days_until = (deadline - now).days
                if 0 < days_until <= 7:
                    reminders.append(f"{project} deadline in {days_until} days!")
            except:
                pass
    
    return reminders[:5]  # Return top 5 reminders

# === Internet Access Functions ===
def search_web(query, num_results=3):
    """Search the web using DuckDuckGo with caching and improved error handling"""
    global search_cache
    
    # Check cache first
    cache_key = query.lower().strip()
    if cache_key in search_cache:
        print(f"📦 Using cached search results for: {query[:50]}...")
        return search_cache[cache_key]
    
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"🔍 Searching web for: {query[:50]}...")
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for result in soup.find_all('div', class_='result')[:num_results]:
            title_tag = result.find('a', class_='result__a')
            snippet_tag = result.find('a', class_='result__snippet')
            
            if title_tag and snippet_tag:
                title = title_tag.get_text(strip=True)
                snippet = snippet_tag.get_text(strip=True)
                url = title_tag.get('href', '')
                
                # Clean up snippet - limit length
                if len(snippet) > 200:
                    snippet = snippet[:200] + '...'
                
                results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet
                })
        
        # Cache results (limit cache size to 20 entries)
        if len(search_cache) > 20:
            # Remove oldest entry
            search_cache.pop(next(iter(search_cache)))
        search_cache[cache_key] = results
        
        return results
    except requests.exceptions.ConnectionError:
        print(f"⚠️ No internet connection available")
        return None  # Return None to indicate connection error
    except requests.exceptions.Timeout:
        print(f"⚠️ Web search timed out (15s)")
        return None
    except Exception as e:
        print(f"⚠️ Web search error: {type(e).__name__}: {str(e)[:50]}")
        return None

def fetch_url_content(url):
    """Fetch and extract main content from a URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit to first 2000 characters
        return text[:2000] if text else "Could not extract content from URL"
    except Exception as e:
        print(f"URL fetch error: {e}")
        return f"Error fetching URL: {str(e)}"

def check_if_needs_internet(query):
    """Determine if a query needs internet search with improved precision"""
    query_lower = query.lower().strip()
    
    # Exclude short conversational queries
    if len(query_lower) < 10:
        return False
    
    # Exclude common conversational patterns that don't need search
    conversational_patterns = [
        'how are you', 'thank you', 'thanks', 'okay', 'ok', 'yes', 'no',
        'i see', 'got it', 'understand', 'appreciate', 'nice', 'good',
        'tell me about yourself', 'who are you', 'what can you do'
    ]
    
    for pattern in conversational_patterns:
        if pattern in query_lower:
            return False
    
    # Strong internet indicators (high confidence)
    strong_keywords = [
        'latest news', 'current events', "today's", 'right now',
        'weather in', 'stock price', 'search for', 'look up',
        'find information', 'google', 'recent news'
    ]
    
    for keyword in strong_keywords:
        if keyword in query_lower:
            return True
    
    # Moderate internet indicators (check with context)
    moderate_keywords = [
        'what is', 'who is', 'where is', 'when is', 'how to',
        'latest', 'news', 'current', 'price', 'website', 'tutorial'
    ]
    
    # Only trigger if query starts with these or they're prominent
    for keyword in moderate_keywords:
        if query_lower.startswith(keyword) or f' {keyword} ' in f' {query_lower} ':
            # Additional check: avoid triggering for definitions we likely know
            if 'what is' in query_lower and any(word in query_lower for word in ['love', 'happiness', 'life', 'ai', 'computer']):
                return False
            return True
    
    return False

# Voice Assistant Functions
def listen_for_voice():
    """Listen for voice input and convert to text"""
    global user_query, listening, processing
    
    if not ENABLE_VOICE_ASSISTANT or not gemini_enabled:
        return
    
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            listening = True
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=30)
            listening = False
            processing = True
            
            try:
                query = recognizer.recognize_google(audio)
                user_query = query
                print(f"You said: {query}")
                get_gemini_response(query)
            except sr.UnknownValueError:
                print("Could not understand audio")
                processing = False
            except sr.RequestError as e:
                print(f"Speech recognition error: {e}")
                processing = False
    except Exception as e:
        print(f"Microphone error: {e}")
        listening = False
        processing = False

def get_gemini_response(query):
    """Get response from Gemini API with optimized memory and internet access"""
    global assistant_response, processing, conversation_history, conversation_summary, user_query
    
    try:
        # Check if this is a notepad command
        note_content = check_notepad_command(query)
        if note_content:
            add_notepad_entry(note_content)
            assistant_response = "Got it! Note saved to your notepad."
            user_query = ""  # Clear the query
            processing = False
            return
        
        # Check if query needs internet search
        web_context = ""
        internet_available = True
        
        if check_if_needs_internet(query):
            print("🌐 Query requires internet search...")
            search_results = search_web(query, num_results=3)
            
            if search_results is None:
                # Connection error - no internet
                internet_available = False
                web_context = "\n[SYSTEM: Internet search attempted but no connection available. Provide answer from training knowledge and inform user internet is unavailable.]\n"
            elif search_results:
                # Found results - format concisely
                web_context = "\n\n[REAL-TIME WEB RESULTS]:\n"
                for i, result in enumerate(search_results, 1):
                    web_context += f"{i}. {result['title']}\n{result['snippet']}\n"
                web_context += "[Use these current results to answer accurately.]\n"
                print(f"✅ Found {len(search_results)} results")
            else:
                # No results found
                web_context = "\n[SYSTEM: Web search found no results. Use training knowledge.]\n"
        
        # === MEMORY OPTIMIZATION ===
        # Get current context stats
        stats = get_context_stats(conversation_history)
        print(f"📊 Memory: {stats['user_messages']} exchanges, ~{stats['total_tokens']} tokens")
        
        # Build optimized context
        if ENABLE_AUTO_SUMMARIZATION and len(conversation_history) > RECENT_CONVERSATION_COUNT:
            # Split into recent and old conversations
            old_conversations = conversation_history[:-RECENT_CONVERSATION_COUNT]
            recent_conversations = conversation_history[-RECENT_CONVERSATION_COUNT:]
            
            # Summarize old conversations if not already done
            if not conversation_summary and old_conversations:
                conversation_summary = create_conversation_summary(old_conversations, max_length=300)
                print(f"📝 Created summary of {len(old_conversations)} old messages")
            
            # Build context with summary + recent
            if conversation_summary:
                context = f"[Previous context summary: {conversation_summary}]\n\n" + "\n".join(recent_conversations)
            else:
                context = "\n".join(recent_conversations)
        else:
            # Use all history if small enough
            context = "\n".join(conversation_history)
        
        # Apply token budget limit
        context_tokens = estimate_tokens(context)
        web_tokens = estimate_tokens(web_context)
        
        if context_tokens + web_tokens > MAX_CONTEXT_TOKENS:
            print(f"⚠️ Context too large ({context_tokens + web_tokens} tokens), trimming...")
            # Trim context to fit budget (leave room for web context)
            available_tokens = MAX_CONTEXT_TOKENS - web_tokens - 100  # 100 token buffer
            trimmed_history = trim_to_token_budget(conversation_history, available_tokens)
            context = "\n".join(trimmed_history)
            print(f"✂️ Trimmed to {len(trimmed_history)} messages (~{estimate_tokens(context)} tokens)")
        
        # Build system prompt
        if internet_available:
            system_prompt = "You are LUDO, a helpful AI assistant with internet access. Use search results when provided for accurate, current information."
        else:
            system_prompt = "You are LUDO, a helpful AI assistant. Internet access currently unavailable."
        
        # Build full conversation
        if context:
            full_conversation = f"{system_prompt}\n\n{context}\n{web_context}\nUser: {query}\nLUDO:"
        else:
            full_conversation = f"{system_prompt}\n\n{web_context}\nUser: {query}\nLUDO:"
        
        # Final token check
        final_tokens = estimate_tokens(full_conversation)
        print(f"🎯 Sending {final_tokens} tokens to API")
        
        # Send to Gemini
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(full_conversation)
        
        assistant_response = response.text
        
        # Store in conversation history (without web context to save space)
        conversation_history.append(f"User: {query}")
        conversation_history.append(f"LUDO: {assistant_response}")
        
        # Limit conversation history size
        if len(conversation_history) > MAX_CONVERSATION_HISTORY:
            # Move excess to summary before trimming
            if ENABLE_AUTO_SUMMARIZATION:
                excess = conversation_history[:len(conversation_history) - MAX_CONVERSATION_HISTORY]
                if excess:
                    old_summary = conversation_summary
                    new_summary = create_conversation_summary(excess, max_length=200)
                    conversation_summary = f"{old_summary} | {new_summary}" if old_summary else new_summary
                    # Trim summary if too long
                    if len(conversation_summary) > 500:
                        conversation_summary = conversation_summary[-500:]
            
            conversation_history = conversation_history[-MAX_CONVERSATION_HISTORY:]
        
        # Save memory to file
        save_conversation_memory()
        
        print(f"LUDO: {assistant_response}")
        print(f"💾 Memory: {len(conversation_history)//2} exchanges saved, {len(conversation_summary)} chars summarized")
        speak_response(assistant_response)
    except Exception as e:
        print(f"Gemini API error: {e}")
        assistant_response = "I'm sorry, I encountered an error."
    finally:
        processing = False

def detect_emotion(text):
    """Detect emotion from text to adjust voice style (simple version)"""
    text_lower = text.lower()
    
    # Emotion keywords mapping
    if any(word in text_lower for word in ['sorry', 'apologize', 'unfortunately', 'sad', 'disappointed']):
        return 'sad'
    elif any(word in text_lower for word in ['excited', 'amazing', 'wonderful', 'awesome', 'great', '!']):
        return 'excited'
    elif any(word in text_lower for word in ['help', 'understand', 'support', 'care']):
        return 'empathetic'
    elif any(word in text_lower for word in ['happy', 'glad', 'pleased', 'good news']):
        return 'cheerful'
    else:
        return 'friendly'  # Default

def speak_response_azure(text, emotion=None):
    """Convert text to speech using Azure Neural Voices with emotion and SSML"""
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        # Detect emotion if not provided
        if emotion is None:
            emotion = detect_emotion(text)
        
        # Configure Azure Speech
        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION
        )
        
        # Set voice
        speech_config.speech_synthesis_voice_name = AZURE_VOICE_NAME
        
        # Create SSML with emotion and prosody
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
               xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
            <voice name="{AZURE_VOICE_NAME}">
                <mstts:express-as style="{emotion}">
                    <prosody rate="{AZURE_SPEAKING_RATE}" pitch="{AZURE_PITCH}">
                        {text}
                    </prosody>
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        # Create synthesizer
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # Synthesize with SSML
        result = synthesizer.speak_ssml_async(ssml).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"✅ Azure TTS: Spoke with '{emotion}' emotion")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            print(f"❌ Azure TTS canceled: {cancellation.reason}")
            if cancellation.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation.error_details}")
                # Fallback to basic TTS
                speak_response_basic(text)
                
    except ImportError:
        print("⚠️ Azure Speech SDK not installed. Install with: pip install azure-cognitiveservices-speech")
        print("Falling back to basic TTS...")
        speak_response_basic(text)
    except Exception as e:
        print(f"Azure TTS error: {e}")
        # Fallback to basic TTS
        speak_response_basic(text)

def speak_response_basic(text):
    """Convert text to speech using basic pyttsx3 (fallback)"""
    try:
        engine = pyttsx3.init()
        
        # Voice customization options
        voices = engine.getProperty('voices')
        
        # Voice selection using the global setting
        if len(voices) > VOICE_INDEX:
            engine.setProperty('voice', voices[VOICE_INDEX].id)
        
        # Apply global voice settings
        engine.setProperty('rate', VOICE_RATE)
        engine.setProperty('volume', VOICE_VOLUME)
        
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Text-to-speech error: {e}")

def speak_response(text):
    """Main TTS function - routes to VITS, Azure, or basic TTS based on configuration"""
    # Try VITS first (free, high-quality neural voice)
    if USE_VITS_TTS and vits_engine:
        try:
            if vits_engine.speak(text, rate=VITS_SPEAKING_RATE):
                return  # Success
        except Exception as e:
            print(f"⚠️ VITS TTS failed, falling back: {e}")
    
    # Fallback to Azure if configured
    if USE_AZURE_TTS and AZURE_SPEECH_KEY:
        speak_response_azure(text)
    else:
        # Final fallback to basic TTS
        speak_response_basic(text)

def process_text_input(query):
    """Process text input from the chat box"""
    global processing, user_query
    
    # Check if it's a notepad command
    note_content = check_notepad_command(query)
    if note_content:
        add_notepad_entry(note_content)
        return
    
    processing = True
    user_query = query
    print(f"User (text): {query}")
    
    # Get response from Gemini
    get_gemini_response(query)
    
    user_query = ""
    processing = False

def list_available_voices():
    """Print all available voices on the system"""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print("\n=== Available Voices ===")
        for idx, voice in enumerate(voices):
            print(f"{idx}: {voice.name} - {voice.id}")
        print("========================\n")
    except Exception as e:
        print(f"Error listing voices: {e}")

def voice_assistant_thread():
    """Background thread for voice assistant"""
    while True:
        if listening or processing:
            continue
        # This will be triggered by keyboard input in main loop

def hand_tracking_thread():
    if not ENABLE_HAND_TRACKING:
        return
    
    global hand_landmarks_global, hand_closed_global, wrist_screen_pos

    try:
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.6)
        cap = cv2.VideoCapture(0)  # Default Windows webcam
    except Exception as e:
        print(f"Hand tracking initialization failed: {e}")
        return

    while True:
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)

        if ENABLE_HAND_TRACKING:
            results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                hand_landmarks_global = hand

                # Determine if hand is closed (fingertips below lower joints)
                tips = [8, 12, 16, 20]
                closed = all(hand.landmark[tip].y > hand.landmark[tip - 2].y for tip in tips)
                hand_closed_global = closed

                # Convert wrist landmark to screen coordinates
                wrist = hand.landmark[0]
                wrist_screen_pos = (int(wrist.x * screen.get_width()), int(wrist.y * screen.get_height()))
            else:
                results = None
                hand_landmarks_global = None
                hand_closed_global = False

def main():
    global track_font, user_query, assistant_response, listening, processing, conversation_history, text_input, input_active  # So you can keep the correct font
    running = True
    fullscreen = False
    frame_idx = 0
    ludo_idx = 0
    gif_scale = 1.0
    gif_width, gif_height = frame_surfaces[0].get_size()
    clock = pygame.time.Clock()
    track_font = pygame.font.Font(font_path, 26)  # Adjust size here
    assistant_font = pygame.font.Font(font_path, 18)  # For displaying conversation
    notepad_font = pygame.font.Font(None, 16)  # Font for notepad entries
    track_update_ms = 3000
    last_track_ms = 0
    threading.Thread(target=hand_tracking_thread, daemon=True).start()
    global ludo_x, ludo_y, grab_active


    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if input_active and text_input.strip():
                        # Send text message
                        query = text_input.strip()
                        text_input = ""
                        input_active = False
                        # Process the query
                        threading.Thread(target=lambda: process_text_input(query), daemon=True).start()
                    else:
                        fullscreen = toggle_fullscreen(screen, fullscreen)
                elif event.key == pygame.K_ESCAPE:
                    if input_active:
                        input_active = False
                        text_input = ""
                    else:
                        running = False
                elif event.key == pygame.K_SPACE:
                    if input_active:
                        # Add space to text input when in typing mode
                        text_input += " "
                    elif not listening and not processing and ENABLE_VOICE_ASSISTANT:
                        # Activate voice assistant with Space bar when not typing
                        threading.Thread(target=listen_for_voice, daemon=True).start()
                elif event.key == pygame.K_x:
                    if not input_active:
                        # Clear chat display only (keep memory) with 'X' key
                        user_query = ""
                        assistant_response = ""
                        print("Chat display cleared (memory preserved)")
                    else:
                        text_input += event.unicode
                elif event.key == pygame.K_c:
                    if not input_active:
                        # Clear conversation memory with 'C' key
                        conversation_history.clear()
                        user_query = ""
                        assistant_response = ""
                        # Delete memory file
                        try:
                            if os.path.exists(MEMORY_FILE):
                                os.remove(MEMORY_FILE)
                        except Exception as e:
                            print(f"Failed to delete memory file: {e}")
                        print("Conversation memory cleared!")
                    else:
                        text_input += event.unicode
                elif event.key == pygame.K_n:
                    if not input_active:
                        # Clear notepad with 'N' key
                        notepad_entries.clear()
                        # Delete notepad file
                        try:
                            if os.path.exists(NOTEPAD_FILE):
                                os.remove(NOTEPAD_FILE)
                        except Exception as e:
                            print(f"Failed to delete notepad file: {e}")
                        print("📝 Notepad cleared!")
                    else:
                        text_input += event.unicode
                elif event.key == pygame.K_BACKSPACE:
                    if input_active:
                        text_input = text_input[:-1]
                elif event.key == pygame.K_TAB:
                    # Toggle text input mode
                    input_active = not input_active
                    if not input_active:
                        text_input = ""
                else:
                    # Add character to text input
                    if input_active and event.unicode.isprintable():
                        text_input += event.unicode

        try:
            if audio_enabled and stream:
                audio_data = stream.read(2048, exception_on_overflow=False)
                volume = get_volume(audio_data)

                scale_factor = 1 + min(volume / 1000, 1)
                gif_scale = 0.9 * gif_scale + 0.1 * scale_factor
            else:
                # No audio, use default scale
                gif_scale = 1.0

            scaled_width = int(gif_width * gif_scale * 0.6)  # Reduced to 60% size
            scaled_height = int(gif_height * gif_scale * 0.6)

            now_ms = pygame.time.get_ticks()
            if now_ms - last_track_ms >= track_update_ms:
                threading.Thread(target=fetch_track, daemon=True).start()
                last_track_ms = now_ms



            # LUDO main face frame
            ludo_main_frame = frame_surfaces[frame_idx]
            ludo_main_scaled = pygame.transform.scale(ludo_main_frame, (scaled_width, scaled_height)).convert_alpha()
            ludo_main_tint = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
            ludo_main_tint.fill(CYAN + (255,))
            ludo_main_scaled.blit(ludo_main_tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            screen.fill((0, 0, 0))

            # Overlay LUDO main face (center position)
            ludo_main_rect = ludo_main_scaled.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
            screen.blit(ludo_main_scaled, ludo_main_rect)

            # Draw Discord icon (below LUDO face)
            discord_x = screen.get_width() // 2 - discord_icon.get_width() // 2
            discord_y = ludo_main_rect.bottom - 50
            screen.blit(discord_icon, (discord_x, discord_y))

            # Time
            now = datetime.datetime.now()
            current_time = now.strftime("%I:%M:%S %p")
            time_surface = clock_font.render(current_time, True, CYAN)
            time_rect = time_surface.get_rect(center=(screen.get_width() // 2, 100))
            screen.blit(time_surface, time_rect)

            # Calendar
            calendar_margin_right = 40
            calendar_cell_width = 35
            calendar_margin_left = 10
            days_in_week = 7
            calendar_width = days_in_week * calendar_cell_width + (days_in_week - 1) * calendar_margin_left
            calendar_x = screen.get_width() - calendar_width - calendar_margin_right
            render_calendar(screen, calendar_x, 60)



            # --- Chat Section (Left Side) ---
            chat_x = 40
            chat_y = 150
            chat_width = screen.get_width() // 3 - 60
            chat_height = screen.get_height() - 320
            
            # Draw chat box background
            chat_bg = pygame.Surface((chat_width, chat_height), pygame.SRCALPHA)
            chat_bg.fill((0, 20, 40, 180))  # Dark blue transparent
            pygame.draw.rect(chat_bg, CYAN, chat_bg.get_rect(), 3)  # Border
            screen.blit(chat_bg, (chat_x, chat_y))
            
            # Chat title
            chat_title = assistant_font.render("LUDO Chat", True, CYAN)
            screen.blit(chat_title, (chat_x + 15, chat_y + 15))
            
            # Display conversation history with text wrapping
            chat_line_y = chat_y + 55
            line_height = 22
            max_text_width = chat_width - 40  # Padding on both sides
            current_y = chat_line_y
            max_y = chat_y + chat_height - 10  # Bottom boundary
            
            # Calculate which messages to show (work backwards from most recent)
            visible_messages = []
            total_height = 0
            
            for msg in reversed(conversation_history):
                if msg.startswith("User:"):
                    prefix = "User: "
                    content = msg[6:]
                    color = (120, 220, 255)
                elif msg.startswith("LUDO:"):
                    prefix = "LUDO: "
                    content = msg[6:]
                    color = CYAN
                else:
                    continue
                
                # Wrap the message text
                wrapped_lines = wrap_text(content, chat_font, max_text_width - 50)
                msg_height = (len(wrapped_lines) + 1) * line_height + 5 
                
                if total_height + msg_height > (max_y - chat_line_y):
                    break
                
                visible_messages.insert(0, {
                    'prefix': prefix,
                    'lines': wrapped_lines,
                    'color': color
                })
                total_height += msg_height
            
            # Draw messages
            current_y = chat_line_y
            for msg_data in visible_messages:
                # Draw prefix (User: or LUDO:)
                prefix_surface = chat_font.render(msg_data['prefix'], True, msg_data['color'])
                screen.blit(prefix_surface, (chat_x + 20, current_y))
                current_y += line_height
                
                # Draw wrapped lines with indentation
                for line in msg_data['lines']:
                    if current_y >= max_y:
                        break
                    line_surface = chat_font.render(line, True, msg_data['color'])
                    screen.blit(line_surface, (chat_x + 35, current_y))
                    current_y += line_height
                
                current_y += 5  # Add spacing between messages
            
            # --- Chat Input Box ---
            input_box_height = 40
            input_box_y = chat_y + chat_height + 10
            input_box_rect = pygame.Rect(chat_x, input_box_y, chat_width, input_box_height)
            
            # Draw input box with different color when active
            if input_active:
                pygame.draw.rect(screen, (0, 40, 60), input_box_rect)
                pygame.draw.rect(screen, CYAN, input_box_rect, 3)
            else:
                pygame.draw.rect(screen, (0, 30, 50), input_box_rect)
                pygame.draw.rect(screen, CYAN, input_box_rect, 2)
            
            # Display typed text or hint
            if input_active or text_input:
                # Show typed text with cursor
                display_text = text_input if len(text_input) < 35 else "..." + text_input[-32:]
                cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
                text_surface = chat_font.render(display_text + cursor, True, CYAN)
                screen.blit(text_surface, (chat_x + 15, input_box_y + 12))
            else:
                # Show hint text
                hint_text = "Press TAB to type or SPACE to talk..."
                hint_surface = chat_font.render(hint_text, True, (100, 100, 100))
                screen.blit(hint_surface, (chat_x + 15, input_box_y + 12))
            
            # --- Voice Assistant Status Display ---
            status_y = screen.get_height() - 120
            if listening:
                status_text = "Listening..."
                status_surface = assistant_font.render(status_text, True, CYAN)
                status_rect = status_surface.get_rect(center=(screen.get_width() // 2, status_y))
                
                # Add pulsing effect
                pulse_size = int(5 * (1 + 0.3 * abs((pygame.time.get_ticks() % 1000) / 500 - 1)))
                pygame.draw.circle(screen, CYAN, (status_rect.left - 20, status_rect.centery), pulse_size)
                
                screen.blit(status_surface, status_rect)
            elif processing:
                status_text = "Processing..."
                status_surface = assistant_font.render(status_text, True, CYAN)
                status_rect = status_surface.get_rect(center=(screen.get_width() // 2, status_y))
                screen.blit(status_surface, status_rect)
            
            # --- Display keyboard shortcuts ---
            if not listening and not processing and ENABLE_VOICE_ASSISTANT and gemini_enabled:
                if input_active:
                    shortcut_text = "Press ENTER to send | ESC to cancel | TAB to exit typing mode"
                else:
                    shortcut_text = "TAB: type | SPACE: talk | X: clear chat | C: clear memory | N: clear notepad"
                shortcut_surface = description_font.render(shortcut_text, True, (120, 120, 120))
                shortcut_rect = shortcut_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() - 30))
                screen.blit(shortcut_surface, shortcut_rect)
            
            # --- Display conversation memory counter ---
            if len(conversation_history) > 0:
                memory_count = len(conversation_history) // 2
                memory_text = f"Memory: {memory_count} conversation(s)"
                memory_surface = description_font.render(memory_text, True, (100, 255, 100))
                memory_rect = memory_surface.get_rect(topright=(screen.get_width() - 20, 20))
                screen.blit(memory_surface, memory_rect)
            
            # --- Display Notepad (bottom-right) ---
            notepad_x = screen.get_width() - 420
            notepad_y = screen.get_height() - 400
            notepad_width = 400
            notepad_height = 380
            
            # Draw notepad container
            notepad_rect = pygame.Rect(notepad_x, notepad_y, notepad_width, notepad_height)
            pygame.draw.rect(screen, (0, 20, 40), notepad_rect)
            pygame.draw.rect(screen, CYAN, notepad_rect, 2)
            
            # Draw notepad title
            notepad_title = description_font.render("Quick Notes", True, CYAN)
            screen.blit(notepad_title, (notepad_x + 10, notepad_y + 10))
            
            # Draw notepad entries
            entry_y = notepad_y + 35
            line_height = 18
            max_chars = 48  # Characters per line
            
            for entry in notepad_entries:
                if entry_y > notepad_y + notepad_height - 30:
                    break  # Stop if we run out of space
                
                # Draw timestamp
                timestamp_text = entry['timestamp'].split()[1][:5]  # Get HH:MM
                timestamp_surface = notepad_font.render(timestamp_text, True, (100, 150, 200))
                screen.blit(timestamp_surface, (notepad_x + 10, entry_y))
                
                # Wrap text if needed
                text = entry['text']
                words = text.split()
                lines = []
                current_line = []
                current_length = 0
                
                for word in words:
                    if current_length + len(word) + 1 <= max_chars:
                        current_line.append(word)
                        current_length += len(word) + 1
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = len(word)
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                # Draw wrapped text lines
                for i, line in enumerate(lines[:3]):  # Max 3 lines per entry
                    if entry_y + (i + 1) * line_height > notepad_y + notepad_height - 30:
                        break
                    line_surface = notepad_font.render(line, True, (200, 220, 255))
                    screen.blit(line_surface, (notepad_x + 60, entry_y + i * line_height))
                
                entry_y += max(len(lines[:3]), 1) * line_height + 10
            
            # Draw notepad hint at bottom
            if len(notepad_entries) == 0:
                hint_text = "Say 'note this' or 'idea:' to add notes"
                hint_surface = notepad_font.render(hint_text, True, (100, 100, 100))
                hint_rect = hint_surface.get_rect(center=(notepad_x + notepad_width // 2, notepad_y + notepad_height // 2))
                screen.blit(hint_surface, hint_rect)

            if hand_landmarks_global:
                # Draw landmarks circles
                for landmark in hand_landmarks_global.landmark:
                    x = int(landmark.x * screen.get_width())
                    y = int(landmark.y * screen.get_height())
                    pygame.draw.circle(screen, CYAN, (x, y), 6)

                # Draw connections
                connections = mp.solutions.hands.HAND_CONNECTIONS
                for connection in connections:
                    start_idx, end_idx = connection
                    start = hand_landmarks_global.landmark[start_idx]
                    end = hand_landmarks_global.landmark[end_idx]
                    start_pos = (int(start.x * screen.get_width()), int(start.y * screen.get_height()))
                    end_pos = (int(end.x * screen.get_width()), int(end.y * screen.get_height()))
                    pygame.draw.line(screen, CYAN, start_pos, end_pos, 3)



            pygame.display.flip()
            frame_idx = (frame_idx + 1) % len(frame_surfaces)
            clock.tick(30)

        except IOError as e:
            print(f"Audio buffer overflowed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    if audio_enabled and stream:
        stream.stop_stream()
        stream.close()
    if p:
        p.terminate()
    pygame.quit()

if __name__ == '__main__':
    # List available voices on startup (check terminal to see options)
    list_available_voices()
    # Load previous conversation memory from file
    load_conversation_memory()
    # Load project context and tracking data
    load_context()
    load_projects()
    # Load notepad entries
    load_notepad()
    main()