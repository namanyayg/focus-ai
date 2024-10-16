"""
focus-ai: a productivity coach that monitors your active window
and provides audio feedback to keep you focused and motivated.

This script continuously checks the currently active window, sends the current
window and recent window history to OpenAI's GPT-3.5-turbo model, generates
a short motivational response, and plays it back.

Key components:
- PyAutoGUI: For getting the active window title
- OpenAI API: For generating contextual responses
- Play.ht API: For text-to-speech conversion
- PyAudio: For audio playback

The script runs indefinitely to provide real-time feedback
to keep you focused and productive.
"""

import time
import os
import logging
from typing import List, Dict, Optional
import pyautogui
import pyaudio
from openai import OpenAI
from pyht import Client
from pyht.client import TTSOptions
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Config:
    """Configuration management class."""
    def __init__(self):
        load_dotenv()
        self.openai_api_key: str = os.getenv('OPENAI_API_KEY', '')
        self.playht_api_key: str = os.getenv('PLAYHT_API_KEY', '')
        self.playht_user_id: str = os.getenv('PLAYHT_USER_ID', '')

        if not all([self.openai_api_key, self.playht_api_key, self.playht_user_id]):
            raise ValueError("Missing required environment variables")

config = Config()


class WindowManager:
    """Manages window-related operations."""
    def __init__(self, max_history: int = 5):
        self.last_windows: List[str] = []
        self.max_history: int = max_history

    def get_current_window(self) -> str:
        """
        Get the title of the currently focused window.

        Returns:
            str: The title of the active window or "Unknown" if not found.
        """
        try:
            return pyautogui.getActiveWindow().title
        except AttributeError:
            return "Unknown"

    def update_window_list(self, window_name: str) -> None:
        """
        Update the list of last focused windows.

        Args:
            window_name (str): The name of the current window to add to the list.
        """
        self.last_windows.append(window_name)
        if len(self.last_windows) > self.max_history:
            self.last_windows.pop(0)


class OpenAIManager:
    """Manages interactions with OpenAI API."""
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def get_response(self, current_window: str, last_windows: List[str]) -> Dict[str, str]:
        """
        Get response from OpenAI based on current and last focused windows.

        Args:
            current_window (str): The name of the currently focused window.
            last_windows (List[str]): List of previously focused windows.

        Returns:
            Dict[str, str]: A dictionary containing the text to speak.
        """
        prompt_text = f"""Act as a productivity military coach.
        You are strict, ironic, sarcastic with the user and will go to extreme lengths to encourage them to work.
        Give max ONE SENTENCE SHORT replies only.
        Make it like a game's mission.
        User's current window is: {current_window} and last windows are: {last_windows}.
        Carefully read and understand the current window, if it is social media like youtube or x.com then SCREAM at them to motivate them to focus on productive work. 
        Otherwise, encourage and compliment them like an army sergeant.
        Add excess of punctuation to clearly indicate audio tone, your output will be used for text-to-speech."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt_text}],
                max_tokens=150,
                temperature=0.7
            )
            return {"say": response.choices[0].message.content}
        except Exception as e:
            logger.error(f"Error getting OpenAI response: {e}")
            return {"say": "Soldier, we're experiencing technical difficulties. Stay focused!"}


class TTSManager:
    """Manages text-to-speech operations."""
    def __init__(self, user_id: str, api_key: str):
        self.tts = Client(user_id=user_id, api_key=api_key)
        self.p = pyaudio.PyAudio()

    def speak_text(self, text: str) -> None:
        """
        Use playht & pyaudio to play the text.

        Args:
            text (str): The text to be spoken.
        """
        logger.info(f"Speaking: {text}")
        text = "   " + text  # Add leading spaces for better speech timing
        options = TTSOptions(
            voice="s3://voice-cloning-zero-shot/cebaa3cf-d1d5-4625-ba20-03dcca3b379f/sargesaad/manifest.json",
            voice_guidance=6,
            text_guidance=0,
            speed=1.2,
            sample_rate=20000
        )

        try:
            audio_stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=20000, output=True)
            for chunk in self.tts.tts(text, options):
                audio_stream.write(chunk)
            audio_stream.stop_stream()
            audio_stream.close()
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")


class FocusAI:
    """Main class for the productivity coach application."""
    def __init__(self):
        self.window_manager = WindowManager()
        self.openai_manager = OpenAIManager(config.openai_api_key)
        self.tts_manager = TTSManager(config.playht_user_id, config.playht_api_key)
        self.last_focused_window: Optional[str] = None

    def run(self) -> None:
        """
        Main function to run focus ai.
        Continuously monitors the active window and provides audio feedback.
        """
        logger.info("Starting Focus AI")
        time.sleep(1)

        while True:
            try:
                current_window = self.window_manager.get_current_window()
                logger.debug(f"Current window: {current_window}")

                if current_window != self.last_focused_window:
                    logger.info(f"Window changed: {current_window}")
                    self.window_manager.update_window_list(current_window)
                    response = self.openai_manager.get_response(current_window, self.window_manager.last_windows)
                    say_text = response['say']
                    self.tts_manager.speak_text(say_text)
                    self.last_focused_window = current_window

                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(5)  # Wait longer if there's an error


if __name__ == "__main__":
    focus_ai = FocusAI()
    focus_ai.run()
