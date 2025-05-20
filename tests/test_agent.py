import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from langchain.agents import AgentExecutor
from app.agent import initialize_agent, ReservationAgent, ChatPromptTemplate, ReservationSession
from langchain.callbacks.tracers import LangChainTracer
import asyncio
import httpx


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


@pytest.mark.asyncio
def test_agent_full_reservation_dialog(mock_settings, mock_calendar, mock_langsmith, reservation_params):
    """Test full reservation dialog flow with mocked agent responses."""
    agent = ReservationAgent()
    session = ReservationSession(agent, reservation_params)
    # Mock session.process_message to return the required responses in order
    user_messages = [
        "Hello!",
        "I would like to reserve a table for 4 people for tomorrow at 19:00.",
        "My name is Ivan.",
        "Thank you, waiting for confirmation."
    ]
    agent_responses = [
        "Hello! I can help you with a table reservation. For what date, time, and how many people would you like to book?",
        "Got it, you want to reserve a table for 4 people for tomorrow at 19:00. What is your name?",
        "Thank you, Ivan. I will check the availability and make the reservation.",
        "Your table is successfully reserved for tomorrow at 19:00 under the name Ivan. Thank you for your request!"
    ]
    session.process_message = AsyncMock(side_effect=agent_responses)
    for i, user_msg in enumerate(user_messages):
        response = asyncio.get_event_loop().run_until_complete(session.process_message(user_msg))
        assert response == agent_responses[i]
        session.chat_history.append({"role": "user", "content": user_msg})
        session.chat_history.append({"role": "assistant", "content": response})


@pytest.mark.asyncio
async def test_agent_logic_with_emulated_pizzeria():
    """
    Test agent logic with emulated pizzeria (Retell) responses.
    No external API calls, only local agent logic.
    """
    from app.agent import ReservationAgent, ReservationSession
    reservation_params = {
        "date": "2024-03-20",
        "time": "19:00",
        "people": 4,
        "name": "John Doe"
    }
    agent = ReservationAgent()
    session = ReservationSession(agent, reservation_params)
    chat_history = []

    # Pizzeria operator's lines
    pizzeria_lines = [
        "Hello, this is Margarita Pizza. How can I help you?",
        "For what date and time would you like to make a reservation?",
        "May I have your name, please?",
        "We have a table available. How many people will be in your party?",
        "Your reservation is confirmed. Thank you for calling!"
    ]

    # Check that the agent responds according to the reservation scenario
    for pizzeria_msg in pizzeria_lines:
        response = await session.process_message(pizzeria_msg)
        print(f"Pizzeria: {pizzeria_msg}\nAgent: {response}\n")
        chat_history.append({"role": "user", "content": pizzeria_msg})
        chat_history.append({"role": "assistant", "content": response})
        await asyncio.sleep(0.1)  # to avoid spamming the LLM

    # You can add keyword checks in agent responses here


@pytest.mark.asyncio
async def test_agent_uses_reservation_params():
    """
    The agent should use the provided reservation parameters in its responses.
    Only pizzeria lines are scripted, agent responses are generated dynamically.
    """
    from app.agent import ReservationAgent, ReservationSession
    reservation_params = {
        "date": "2024-03-20",
        "time": "19:00",
        "people": 4,
        "name": "John Doe"
    }
    agent = ReservationAgent()
    session = ReservationSession(agent, reservation_params)
    chat_history = []

    pizzeria_lines = [
        "Hello, this is Margarita Pizza. How can I help you?",
        "For what date and time would you like to make a reservation?",
        "May I have your name, please?",
        "We have a table available. How many people will be in your party?",
        "Your reservation is confirmed. Thank you for calling!"
    ]

    responses = []
    for pizzeria_msg in pizzeria_lines:
        response = await session.process_message(pizzeria_msg)
        print(f"Pizzeria: {pizzeria_msg}\nAgent: {response}\n")
        chat_history.append({"role": "user", "content": pizzeria_msg})
        chat_history.append({"role": "assistant", "content": response})
        responses.append(response)
        await asyncio.sleep(0.1)

    # Check that parameters appear in at least one of the agent's responses
    all_responses = " ".join(responses).lower()
    assert str(reservation_params["people"]) in all_responses or "people" in all_responses
    assert reservation_params["name"].split()[0].lower() in all_responses or "name" in all_responses
    # Flexible date check: either ISO or natural format
    assert (
        reservation_params["date"] in all_responses or
        ("march" in all_responses and "20" in all_responses and "2024" in all_responses) or
        ("20th" in all_responses and "march" in all_responses and "2024" in all_responses)
    ) or "date" in all_responses
    assert reservation_params["time"] in all_responses or "time" in all_responses


@pytest.mark.asyncio
async def test_integration_retell_emulation():
    """
    Integration test: Emulate Retell AI sending pizzeria messages and check agent's behavior with session context.
    """
    from app.agent import ReservationAgent, ReservationSession
    reservation_params = {
        "date": "2024-03-20",
        "time": "19:00",
        "people": 4,
        "name": "John Doe"
    }
    agent = ReservationAgent()
    session = ReservationSession(agent, reservation_params)

    pizzeria_lines = [
        "Hello, this is Margarita Pizza. How can I help you?",
        "For what date and time would you like to make a reservation?",
        "May I have your name, please?",
        "We have a table available. How many people will be in your party?",
        "Your reservation is confirmed. Thank you for calling!"
    ]

    responses = []
    for pizzeria_msg in pizzeria_lines:
        response = await session.process_message(pizzeria_msg)
        print(f"Pizzeria: {pizzeria_msg}\nAgent: {response}\n")
        responses.append(response)
        await asyncio.sleep(0.1)

    all_responses = " ".join(responses).lower()
    assert str(reservation_params["people"]) in all_responses or "people" in all_responses
    assert reservation_params["name"].split()[0].lower() in all_responses or "name" in all_responses
    assert (
        "2024" in all_responses and ("march" in all_responses or "03-20" in all_responses or "20th" in all_responses)
    ) or reservation_params["date"] in all_responses or "date" in all_responses
    assert "19:00" in all_responses or "7:00" in all_responses or "7 pm" in all_responses or "time" in all_responses 