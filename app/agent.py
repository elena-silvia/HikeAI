from http.client import responses
import os
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
from app.config import load_config
from app.prompts import SYSTEM_PROMPT
from app.tools import(
    read_safety_guidelines,
    get_mountain_weather,
    get_mountain_routes
)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

class MountainAgent:
    def __init__(self):
        self.config = load_config()
        api_key =os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Api key not set")

        self.client = genai.Client(api_key=api_key)

        self.tools = [
            read_safety_guidelines,
            get_mountain_weather,
            get_mountain_routes
        ]

        self.chat= self.client.chats.create(
            model = self.config.model,
            config = types.GenerateContentConfig(
                system_instruction = SYSTEM_PROMPT,
                tools = self.tools,
                temperature=0.2,
            ),
        )
    def send_message(self, message: str) -> str:
        response = self.chat.send_message(message)
        return response.text