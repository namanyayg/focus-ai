import time
import json
import os
from openai import OpenAI
from pyht import Client
from pyht.client import TTSOptions
from dotenv import load_dotenv
import pyautogui
import pyaudio

p = pyaudio.PyAudio()

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PLAYHT_API_KEY = os.getenv('PLAYHT_API_KEY')
PLAYHT_USER_ID = os.getenv('PLAYHT_USER_ID')

# Initialize OpenAI and Play.ht TTS
openai_client = OpenAI(api_key=OPENAI_API_KEY)
tts = Client(
   user_id=PLAYHT_USER_ID,
   api_key=PLAYHT_API_KEY,
)

# Global variable to store last 5 focused windows
last_five_windows = []

def get_current_window():
    """Get the title of the currently focused window using a more reliable cross-platform method."""
    active_window_name = None
    try:
        active_window_name = pyautogui.getActiveWindow().title
    except AttributeError:
        active_window_name = "Unknown"
    return active_window_name

def update_window_list(window_name):
    """Update the list of last five focused windows."""
    last_five_windows.append(window_name)
    if len(last_five_windows) > 5:
        last_five_windows.pop(0)

def get_openai_response(current_window, last_windows):
    """Get response from OpenAI based on current and last focused windows."""
    prompt_text = f"Act as a productivity military coach. \
    You are strict, ironic, sarcastic with the user and will go to extreme lenghts to encourage him to work. \
    Give max ONE SENTENCE SHORT replies only. \
    Make it like a game's mission. \
    User's current window is: {current_window} and last windows are: {last_windows}. \
    Carefully read and understand the current window, if it is social media like youtube or x.com then SCREAM at them to motivate them to focus on productive work. \
    Otherwise, encourage and compliment them like an army sergeant. \
    Add excess of punctuation to clearly indicate audio tone, your output will be used for text-to-speech."
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{ "role": "system", "content": prompt_text }],
        max_tokens=150,
        temperature=0.7
    )
    print(response.choices[0].message.content)
    return {
        "angerLevel": 5,
        "say": response.choices[0].message.content,
    }

def speak_text(text, emotion):
    """Use playht & pyaudio to play the text with a given emotion."""
    print(f"Speaking: {text}")
    options = TTSOptions(
        voice="s3://voice-cloning-zero-shot/cebaa3cf-d1d5-4625-ba20-03dcca3b379f/sargesaad/manifest.json",
        voice_guidance=6,
        text_guidance=0,
        speed=1.2,
        sample_rate=20000
    )
    audio_stream = p.open(format=pyaudio.paInt16, channels=1, rate=20000, output=True)
    for chunk in tts.tts(text, options):
        audio_stream.write(chunk)
    audio_stream.stop_stream()
    audio_stream.close()

def main():
    last_focused_window = None
    i = 0
    time.sleep(1)
    while i < 100:
        i = i+1
        current_window = get_current_window()
        print(f"Current window: {current_window}")
        if current_window != last_focused_window:
            print(f"Last focused window: {last_focused_window}")
            update_window_list(current_window)
            response = get_openai_response(current_window, last_five_windows)
            anger_level = response['angerLevel']
            say_text = response['say']
            emotion = 'angry' if anger_level > 5 else 'calm'
            speak_text(say_text, emotion)
            last_focused_window = current_window
        time.sleep(1)

if __name__ == "__main__":
    main()


