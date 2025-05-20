import pytest
import os
from unittest.mock import Mock


@pytest.fixture(autouse=True)
def mock_env_variables():
    """Mock environment variables for testing."""
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    yield
    os.environ.pop("OPENAI_API_KEY", None)


@pytest.fixture
def mock_openai():
    """Mock OpenAI API responses."""
    with pytest.MonkeyPatch.context() as m:
        m.setattr("openai.ChatCompletion.create", Mock(return_value={
            "choices": [{
                "message": {
                    "content": "Test response",
                    "role": "assistant"
                }
            }]
        }))
        yield m 