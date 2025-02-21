import os
import tempfile
import logging
from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set logging level for whisper
logging.getLogger("whisper").setLevel(logging.WARNING)

load_dotenv()
client = OpenAI()

def transcribe_audio(audio_data: bytes) -> str:
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OPENAI_API_KEY is not set in environment variables")

    #logger.debug(f"Received audio data of size: {len(audio_data)} bytes")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
        temp_file.write(audio_data)
        temp_file_path = temp_file.name
        #logger.debug(f"Saved audio to temporary file: {temp_file_path}")
    
    try:
        with open(temp_file_path, "rb") as audio_file:
            #logger.debug("Sending request to OpenAI API")
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            #logger.debug(f"Received transcription: {transcription}")
            return transcription
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}")
        raise
    finally:
        try:
            os.unlink(temp_file_path)
            #logger.debug("Cleaned up temporary file")
        except Exception as e:
            logger.error(f"Error cleaning up temp file: {str(e)}")