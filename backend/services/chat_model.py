import os
from openai import OpenAI
from dotenv import load_dotenv
import logging
from pathlib import Path

# Disable openai module debug logs
logging.getLogger("openai").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
load_dotenv()

client = OpenAI()

def get_chat_response(user_input: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful, friendly assistant."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise

def text_to_speech(text: str) -> str:
    try:
        # Create audio directory if it doesn't exist
        static_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "static" / "audio"
        static_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename based on text content
        filename = f"response_{hash(text)}.mp3"
        filepath = static_dir / filename
        
        # Generate speech only if file doesn't exist
        if not filepath.exists():
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
                input=text
            )
            response.stream_to_file(str(filepath))
            logger.info(f"Generated new audio file: {filepath}")
            
        return f"/static/audio/{filename}"
    except Exception as e:
        logger.error(f"Error in text-to-speech: {str(e)}")
        raise
