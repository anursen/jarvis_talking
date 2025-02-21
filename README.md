# Jarvis Home Assistant Voice Interface

A voice-controlled interface for Home Assistant using OpenAI's GPT-4, Whisper, and Text-to-Speech APIs.

## Features

- Voice command recognition using OpenAI Whisper
- Natural language processing with GPT-4
- Text-to-speech responses using OpenAI TTS
- Integration with Home Assistant
- Persistent session management
- HTTPS support with local certificates
- Cross-device access within local network

## Prerequisites

- Python 3.9+
- OpenAI API key
- Home Assistant instance with API access
- Modern web browser with microphone support

## Installation

1. Clone the repository and create a virtual environment:
```bash
git clone [repository-url]
cd jarvis_talking
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and Home Assistant details
```

4. Generate SSL certificates:
```bash
cd certs
./generate-certs.sh
# Follow the instructions to install the CA certificate
```

## Usage

1. Start the server:
```bash
python backend/main.py
```

2. Access the interface:
- Locally: https://localhost:8000
- From other devices: https://[your-ip]:8000

3. Using the interface:
- Click and hold the "Hold to Talk" button while speaking
- Release to send your command
- Wait for Jarvis to process and respond

## Development

- Frontend code is in `/frontend/static/`
- Backend API is in `/backend/`
- Home Assistant tools are in `/backend/utils/agent_tools.py`

## Configuration

### SSL Certificates
- Located in `/certs/`
- Configure domains in `local-cert.conf`
- Run `generate-certs.sh` to create new certificates

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `HA_TOKEN`: Home Assistant long-lived access token
- `HA_URL`: Home Assistant instance URL

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - See LICENSE file for details
