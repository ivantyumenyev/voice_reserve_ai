# Voice Reserve AI

An AI-powered restaurant reservation system that uses voice calls to handle table bookings automatically. The system integrates with Rettel.ai for voice calls, LangChain for intelligent conversation handling, and is designed for Google Calendar integration (currently in-memory calendar logic, easily extendable).

## Features

- 🎙️ Voice-based restaurant table reservation system
- 🤖 AI-powered conversation handling with LangChain
- 📞 Integration with Rettel.ai for voice calls
- 📅 In-memory calendar management (Google Calendar integration ready)
- 🔄 Real-time availability checking
- 📊 Reservation management and tracking
- 🔒 Secure handling of sensitive data
- 🧑‍💻 LangSmith tracing for agent monitoring and debugging

## Tech Stack

- **Backend**: Python 3.11+
- **Framework**: FastAPI
- **AI/ML**: LangChain, OpenRouter API
- **Voice**: Rettel.ai SDK
- **Calendar**: In-memory (Google Calendar API ready)
- **Tracing**: LangSmith
- **Testing**: pytest
- **Linting**: flake8
- **Containerization**: Docker

## Prerequisites

- Python 3.11 or higher
- OpenRouter API key
- Rettel.ai API key
- Google Calendar API credentials (for future integration)
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
   Edit `.env` and fill in your API keys and configuration. **All sensitive data and configuration must be set via environment variables.**

5. (Optional) Set up Google Calendar credentials for future integration:
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
│   ├── main.py             # FastAPI application and API endpoints
│   ├── agent.py            # LangChain agent logic, tools, and LangSmith tracing
│   ├── calendar.py         # In-memory reservation calendar logic (Google Calendar ready)
│   ├── config.py           # Configuration and environment variable management
├── tests/                  # All test files and fixtures
│   ├── test_agent.py       # Agent logic and conversation flow tests
│   ├── test_langsmith.py   # LangSmith tracing and integration tests
│   ├── conftest.py         # Test fixtures and environment mocks
├── requirements.txt        # Main dependencies
├── requirements-dev.txt    # Development dependencies (pytest, etc.)
├── Dockerfile              # Container configuration
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── .flake8                 # Linting configuration
├── .cursor/                # Cursor IDE rules and project standards
└── README.md               # Project documentation
```

## Environment Variables

Create a `.env` file with the following variables (see `.env.example`):
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `RETELL_API_KEY`: Your Rettel.ai API key
- `GOOGLE_CREDENTIALS_PATH`: Path to Google Calendar credentials (for future integration)
- `DEBUG`: Enable debug mode (True/False)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

- All tests are located in the `tests/` directory and use `pytest`.
- Use `pytest` for unit and integration tests:
  ```bash
  pytest
  ```
- Test coverage includes agent logic, calendar logic, LangSmith tracing, and Retell integration.
- Use `conftest.py` for fixtures and environment mocks.

## Docker

Build and run with Docker:
```bash
docker build -t voice-reserve-ai .
docker run -p 8000:8000 voice-reserve-ai
```

## Cursor Rules

- The project uses [Cursor](https://www.cursor.so/) for code navigation and standards.
- All project rules and best practices are in `.cursor/rules/`.
- See `README.md` and Cursor rules for up-to-date documentation and guidelines.

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
- [LangSmith](https://smith.langchain.com/)
- [Cursor](https://www.cursor.so/) 