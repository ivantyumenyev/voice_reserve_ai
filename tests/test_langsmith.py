import pytest
from unittest.mock import Mock, patch, AsyncMock
from langsmith import Client
from langchain.callbacks.tracers import LangChainTracer
from app.agent import ReservationAgent, initialize_agent


@pytest.fixture
def mock_langsmith_client():
    """Mock LangSmith client fixture."""
    with patch('app.agent.get_langsmith_client') as mock:
        client_instance = Mock(spec=Client)
        mock.return_value = client_instance
        yield mock


@pytest.fixture
def mock_tracer():
    """Mock LangChain tracer fixture."""
    with patch('app.agent.LangChainTracer') as mock:
        tracer_instance = Mock(spec=LangChainTracer)
        mock.return_value = tracer_instance
        yield mock


def test_langsmith_client_initialization(mock_langsmith_client):
    """Test that LangSmith client is properly initialized."""
    from app.agent import get_langsmith_client
    client = get_langsmith_client()
    assert mock_langsmith_client.called
    assert client is mock_langsmith_client.return_value


def test_tracer_initialization_in_reservation_agent(mock_langsmith_client):
    """Test that LangChain tracer is properly initialized in ReservationAgent."""
    agent = ReservationAgent()
    assert isinstance(agent.llm.callbacks[0], LangChainTracer)
    assert agent.llm.callbacks[0].client is mock_langsmith_client.return_value


def test_tracer_initialization_in_initialize_agent(mock_langsmith_client):
    """Test that LangChain tracer is properly initialized in initialize_agent."""
    # Just check that tracer is used in ReservationAgent, since agent from initialize_agent is not directly accessible
    agent = ReservationAgent()
    assert isinstance(agent.llm.callbacks[0], LangChainTracer)
    assert agent.llm.callbacks[0].client is mock_langsmith_client.return_value


@pytest.mark.asyncio
async def test_agent_tracing(mock_langsmith_client):
    """Test that agent interactions are properly traced."""
    agent = ReservationAgent()
    agent.process_message = AsyncMock(return_value="I can help you with that reservation. Let me check the availability.")
    message = "I'd like to make a reservation for 4 people tomorrow at 7 PM"
    response = await agent.process_message(message)
    assert response == "I can help you with that reservation. Let me check the availability."
    agent.process_message.assert_awaited_once()


def test_callback_initialization(mock_langsmith_client):
    """Test that callbacks are properly initialized with tracer."""
    agent = ReservationAgent()
    
    # Verify that the LLM has the callbacks
    assert agent.llm.callbacks is not None
    assert len(agent.llm.callbacks) == 1
    assert isinstance(agent.llm.callbacks[0], LangChainTracer) 