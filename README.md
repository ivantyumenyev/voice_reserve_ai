# Voice Reserve AI

An AI-powered restaurant reservation system that uses voice calls to handle table bookings automatically. The system integrates with Rettel.ai for voice calls, LangChain for intelligent conversation handling, and Google Calendar for reservation management.

## Features

- 🎙️ Voice-based restaurant table reservation system
- 🤖 AI-powered conversation handling with LangChain
- 📞 Integration with Rettel.ai for voice calls
- 📅 Google Calendar integration for reservation management
- 🔄 Real-time availability checking
- 📊 Reservation management and tracking
- 🔒 Secure handling of sensitive data

## Tech Stack

- **Backend**: Python 3.11+
- **Framework**: FastAPI
- **AI/ML**: LangChain, OpenRouter API
- **Voice**: Rettel.ai SDK
- **Calendar**: Google Calendar API
- **Testing**: pytest
- **Linting**: flake8
- **Containerization**: Docker

## Prerequisites

- Python 3.11 or higher
- OpenRouter API key
- Rettel.ai API key
- Google Calendar API credentials
- Docker (optional)

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/voice-reserve-ai.git
   cd voice-reserve-ai
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your API keys and configuration.

5. Set up Google Calendar credentials:
   - Place your `google_credentials.json` in the project root
   - Follow Google Calendar API setup instructions

## Development

1. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Run linting:
   ```bash
   flake8
   ```

## Project Structure

```
voice-reserve-ai/
├── app/
│   ├── __init__.py         # Package initialization
│   ├── main.py            # FastAPI application
│   ├── agent.py           # LangChain agent implementation
│   ├── calendar.py        # Calendar management
│   ├── config.py          # Configuration management
│   └── ...
├── tests/                 # Test directory
├── .cursor/              # Cursor IDE rules
├── requirements.txt      # Project dependencies
├── Dockerfile           # Container configuration
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore rules
└── README.md           # Project documentation
```

## Environment Variables

Create a `.env` file with the following variables:
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `RETELL_API_KEY`: Your Rettel.ai API key
- `GOOGLE_CREDENTIALS_PATH`: Path to Google Calendar credentials
- `DEBUG`: Enable debug mode (True/False)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

The project uses pytest for testing. Run tests with:
```bash
pytest
```

## Docker

Build and run with Docker:
```bash
docker build -t voice-reserve-ai .
docker run -p 8000:8000 voice-reserve-ai
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain)
- [Rettel.ai](https://retellai.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Google Calendar API](https://developers.google.com/calendar) 