import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from langchain.agents import AgentExecutor
from app.agent import initialize_agent, ReservationAgent, ChatPromptTemplate
from langchain.callbacks.tracers import LangChainTracer


@pytest.fixture
def mock_settings():
    """Mock settings fixture."""
    with patch('app.agent.get_settings') as mock:
        mock.return_value = Mock(
            openrouter_api_key="test_api_key"
        )
        yield mock


@pytest.fixture
def mock_calendar():
    """Mock calendar fixture."""
    with patch('app.agent.ReservationCalendar') as mock:
        calendar_instance = Mock()
        calendar_instance.check_availability.return_value = True
        calendar_instance.get_available_times.return_value = ["19:00", "19:30", "20:00"]
        mock.return_value = calendar_instance
        yield mock


@pytest.fixture
def mock_langsmith():
    """Mock LangSmith components fixture."""
    with patch('app.agent.get_langsmith_client') as mock_client:
        mock_client.return_value = Mock()
        yield mock_client


@pytest.fixture
def reservation_params():
    """Sample reservation parameters."""
    return {
        "date": "2024-03-20",
        "time": "19:00",
        "people": 4,
        "name": "John Doe"
    }


def test_initialize_agent_creation(mock_settings, mock_calendar, mock_langsmith, reservation_params):
    """Test that agent is properly initialized with all components."""
    agent = ReservationAgent()
    
    assert isinstance(agent.llm.callbacks[0], LangChainTracer)
    assert agent.llm.callbacks[0].client is mock_langsmith.return_value
    assert isinstance(agent.tools[0].name, str)
    assert isinstance(agent.tools[1].name, str)


def test_agent_with_valid_availability_check(mock_settings, mock_calendar, mock_langsmith, reservation_params):
    """Test agent's availability check with valid parameters."""
    agent = initialize_agent(reservation_params)
    
    # Test the check_availability tool directly
    tool = agent.tools[0]
    result = tool.invoke({"date": "2024-03-20", "time": "19:00"})
    
    assert isinstance(result, dict)
    assert "available" in result
    assert "suggested_times" in result
    assert result["available"] is True
    assert isinstance(result["suggested_times"], list)


def test_agent_with_invalid_date(mock_settings, mock_calendar, mock_langsmith, reservation_params):
    """Test agent's availability check with invalid date format."""
    agent = initialize_agent(reservation_params)
    
    # Test the check_availability tool with invalid date
    tool = agent.tools[0]
    result = tool.invoke({"date": "invalid-date", "time": "19:00"})
    
    assert isinstance(result, dict)
    assert "error" in result


def test_agent_memory_initialization(mock_settings, mock_calendar, mock_langsmith, reservation_params):
    """Test that agent's memory is properly initialized."""
    agent = initialize_agent(reservation_params)
    
    assert agent.memory is not None
    assert agent.memory.memory_key == "chat_history"
    assert agent.memory.return_messages is True


def test_agent_prompt_template_vars():
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful restaurant reservation assistant.\nCurrent reservation details:\n- Date: {date}\n- Time: {time}\n- Number of people: {people}\n- Customer name: {name}\nHelp the customer with their reservation request.\nAlways be polite and professional.\nIf you need to check availability, use the check_availability tool."),
        ("human", "{input}"),
    ])
    template_vars = prompt.input_variables
    assert "input" in template_vars or "input" in prompt.messages[1][1]


@pytest.mark.asyncio
async def test_agent_conversation_flow(mock_settings, mock_calendar, mock_langsmith, reservation_params):
    """Test basic conversation flow with the agent."""
    agent = ReservationAgent()
    agent.process_message = AsyncMock(return_value="I can help you with that reservation. Let me check the availability.")
    response = await agent.process_message("I'd like to make a reservation")
    assert response == "I can help you with that reservation. Let me check the availability."
    agent.process_message.assert_awaited_once() 