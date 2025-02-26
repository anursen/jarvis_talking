import sys
from pathlib import Path

# Add the project root directory to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langchain_core.messages import  HumanMessage, SystemMessage
from backend.utils.agent_tools import (
    ha_get_entities_containing, 
    ha_get_state_of_a_specific_entity, 
    ha_get_entity_history, 
    ha_get_logbook
)

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.services.whisper_model import transcribe_audio
from backend.services.chat_model import text_to_speech
import uvicorn
import os
import logging
from datetime import datetime, timedelta

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))


# Add both project roots to Python path
voice_app_path = Path("/Users/anursen/Documents/voice-to-text-app")
jarvis_path = Path("/Users/anursen/Documents/jarvis")
for path in [str(voice_app_path), str(jarvis_path)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Set logging to only show warnings and errors
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Disable all debug logs we don't want to see
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.disabled = True
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("python_multipart").setLevel(logging.WARNING)
logging.getLogger("multipart").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)  # Add this line
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)  # Add this line

app = FastAPI()

# Update CORS middleware with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://localhost:8000",
        "https://127.0.0.1:8000",
        f"https://{os.getenv('LOCAL_IP', 'localhost')}:8000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Specify allowed methods
    allow_headers=["*"],
)

# Mount static files with absolute path
static_dir = Path(__file__).resolve().parent.parent / "frontend" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def read_root():
    templates_dir = static_dir / "templates" / "index.html"
    return FileResponse(str(templates_dir))


# Add the parent directory to sys.path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir.parent  # This should point to the 'src' directory
sys.path.append(str(src_dir))

# Global session storage
class ChatSession:
    def __init__(self):
        self.storage = MemorySaver()
        self.last_access = datetime.now()

class SessionManager:
    def __init__(self, session_timeout_minutes=30):
        self.sessions = {}
        self.timeout = timedelta(minutes=session_timeout_minutes)
        self.last_cleanup = datetime.now()

    def get_session(self, session_id: str) -> ChatSession:
        # Periodic cleanup (every 5 minutes)
        if datetime.now() - self.last_cleanup > timedelta(minutes=5):
            self._cleanup_expired_sessions()
            self.last_cleanup = datetime.now()
        
        # Create new session if it doesn't exist
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession()
            logger.info(f"Created new session: {session_id}")
        
        # Update last access time
        self.sessions[session_id].last_access = datetime.now()
        return self.sessions[session_id]

    def _cleanup_expired_sessions(self):
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if current_time - session.last_access > self.timeout
        ]
        for session_id in expired_sessions:
            logger.info(f"Removing expired session: {session_id}")
            del self.sessions[session_id]

# Initialize session manager at app level
session_manager = SessionManager()

async def jarvis_with_memory(human_message: str, system_message, user_id, user_storage):
    # Comment out debug print
    # print(user_storage)
    '''User Storage is a MemorySaver '''
    #TODO memory storage only available in session level. No hard memory available
    #TODO No session level memory available,    
    llm = ChatOpenAI(model="gpt-4o-mini")
    tools = [ha_get_entities_containing
            ,ha_get_state_of_a_specific_entity
            ,ha_get_entity_history
            ,ha_get_logbook]

    llm_with_tools = llm.bind_tools(tools)

    # System message
    sys_msg = SystemMessage(
        content="You are Jarvis, a smart home assistant designed to help with managing home devices and providing information about their statuses. "
                "You have access to the Home Assistant API through various tools. "
                "You can perform the following tasks: "
                "1. Query Home Assistant for a list of entities in the home. "
                "2. Retrieve the current status of any entity. "
                "3. Get the historical data of an entity to analyze past behaviors. "
                f"Always provide accurate and concise information while ensuring a {system_message} tone.")

    # Node
    async def assistant(state: MessagesState):
        return {"messages": [await llm_with_tools.ainvoke([sys_msg] + state["messages"])]}


    # Graph
    builder = StateGraph(MessagesState)

    # Define nodes: these do the work
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))

    # Define edges: these determine how the control flow moves
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
        # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
        tools_condition,
    )
    builder.add_edge("tools", "assistant")


    # Show
    #display(Image(react_graph.get_graph(xray=True).draw_mermaid_png()))



    react_graph_memory = builder.compile(checkpointer=user_storage)

    # Specify a thread
    config = {"configurable": {"thread_id": user_id}}

    # Specify an input
    messages = [HumanMessage(content=human_message)]

        # Run
    messages = await react_graph_memory.ainvoke({"messages": messages},config)
    #for m in messages['messages']:
    #    m.pretty_print()


    return messages['messages'][-1].content


@app.post("/chat/")
async def chat(session_id: str = "default", file: UploadFile = File(...)):  # Fixed parameter order
    try:
        if not session_id:
            return JSONResponse(
                content={"error": "No session ID provided"},
                status_code=400
            )
            
        # Get existing session or create new one
        session = session_manager.get_session(session_id)
        user_id = session_id
        system_message = "Mechanical like a jarvis AI"
        audio_data = await file.read()
        transcription = transcribe_audio(audio_data)
        # Use session's storage for memory persistence
        response = await jarvis_with_memory(
            transcription,
            system_message,
            user_id,
            session.storage  # Use session's persistent storage
        )
        
        # Generate audio response
        audio_path = text_to_speech(response)
        
        return JSONResponse(content={
            "transcription": transcription,
            "response": response,
            "audio": audio_path,  # This will be something like "/static/audio/response_123456.mp3"
            "session_id": session_id
        })
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    try:
        current_dir = Path(__file__).resolve().parent
        root_dir = current_dir.parent
        ssl_keyfile = root_dir / "certs" / "key.pem"
        ssl_certfile = root_dir / "certs" / "cert.pem"
        
        if not ssl_keyfile.exists() or not ssl_certfile.exists():
            raise FileNotFoundError(f"SSL certificates not found at {ssl_keyfile} or {ssl_certfile}")
            
        local_ip = os.getenv('LOCAL_IP', '0.0.0.0')  # Listen on all interfaces
        print(f"Starting server on {local_ip}:8000")
        print(f"Access locally via: https://localhost:8000")
        print(f"Access from network via: https://{local_ip}:8000")

        uvicorn.run(
            "main:app",
            host="0.0.0.0",  # Changed from localhost to listen on all interfaces
            port=8000,
            reload=False,
            reload_excludes=["*.mp3", "*.wav", "*.audio/*"],
            ssl_keyfile=str(ssl_keyfile),
            ssl_certfile=str(ssl_certfile),
            ssl_keyfile_password=None
        )
    except Exception as e:
        print(f"Failed to start server: {e}")
