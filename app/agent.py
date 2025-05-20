from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain.tools import tool
from langchain.memory import ConversationBufferMemory
from typing import List, Dict, Any, Tuple
from datetime import datetime
from langsmith import Client
from langchain.callbacks.tracers import LangChainTracer
from langchain.callbacks.manager import CallbackManager

from app.config import get_settings
from app.calendar import ReservationCalendar

def get_langsmith_client():
    return Client()

class ReservationAgent:
    """
    Stateless agent factory for handling restaurant reservations.
    This agent does NOT store any reservation data. All reservation/session data must be passed to ReservationSession.
    """
    def __init__(self):
        self.settings = get_settings()
        tracer = LangChainTracer(
            project_name="restaurant-reservation-agent",
            client=get_langsmith_client()
        )
        self.llm = ChatOpenAI(
            api_key=self.settings.openrouter_api_key,
            model="openai/gpt-4o",
            temperature=0.7,
            base_url="https://openrouter.ai/api/v1",
            callbacks=[tracer]
        )
        self.tools = self._create_tools()

    def _create_tools(self) -> List:
        """Create tools for the agent."""
        @tool
        def check_availability(date: str, party_size: int) -> Dict[str, Any]:
            """Check table availability for a given date and party size."""
            return {
                "available": True,
                "suggested_times": ["19:00", "19:30", "20:00"]
            }
        
        @tool
        def make_reservation(
            date: str,
            time: str,
            party_size: int,
            name: str
        ) -> Dict[str, Any]:
            """Make a reservation for the given details."""
            return {
                "success": True,
                "reservation_id": "12345",
                "confirmation_message": (
                    f"Reservation confirmed for {name} on {date} at {time}"
                )
            }
        
        return [check_availability, make_reservation]

    def build_prompt(self, reservation_params: Dict[str, Any]) -> ChatPromptTemplate:
        """
        Build a session-specific prompt with reservation parameters.
        The agent is always the caller, making a reservation with these details.
        """
        return ChatPromptTemplate.from_messages([
            ("system", f"""You are a helpful restaurant reservation assistant.\nYou are calling the restaurant to make a reservation with the following details:\n- Date: {reservation_params.get('date', '')}\n- Time: {reservation_params.get('time', '')}\n- Number of people: {reservation_params.get('people', '')}\n- Customer name: {reservation_params.get('name', '')}\nYour goal is to make this reservation. Always be polite and professional.\nYou have access to the following tools:\n- check_availability: Check if a table is available for a given date and party size\n- make_reservation: Make a reservation with the provided details\nUse these tools to help you make the reservation."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def create_agent_with_prompt(self, prompt: ChatPromptTemplate) -> AgentExecutor:
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True
        )

class ReservationSession:
    """
    Session for a single reservation dialog.
    Stores reservation parameters and chat history. All context is session-local.
    """
    def __init__(self, agent: ReservationAgent, reservation_params: dict):
        self.agent = agent
        self.reservation_params = reservation_params
        self.chat_history = []

    async def process_message(self, message: str) -> str:
        prompt = self.agent.build_prompt(self.reservation_params)
        temp_agent = self.agent.create_agent_with_prompt(prompt)
        response = await temp_agent.ainvoke({
            "input": message,
            "chat_history": self.chat_history
        })
        self.chat_history.append({"role": "user", "content": message})
        self.chat_history.append({"role": "assistant", "content": response["output"]})
        return response["output"]

def initialize_agent(reservation_params: Dict[str, Any]) -> AgentExecutor:
    """
    Initialize a LangChain agent for handling voice reservations.
    
    Args:
        reservation_params: Dictionary containing reservation parameters
            (date, time, people, name)
    
    Returns:
        AgentExecutor: Configured agent for handling reservations
    """
    settings = get_settings()
    
    # Configure LangSmith tracing
    tracer = LangChainTracer(
        project_name="restaurant-reservation-agent",
        client=get_langsmith_client()
    )
    
    # Initialize LLM with OpenRouter
    llm = ChatOpenAI(
        api_key=settings.openrouter_api_key,
        model="openai/gpt-4o",
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1",
        callbacks=[tracer]
    )
    
    # Create calendar instance
    calendar = ReservationCalendar()
    
    # Define tools
    @tool
    def check_availability(date: str, time: str) -> Dict[str, Any]:
        """Check table availability for a given date and time."""
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            is_available = calendar.check_availability(
                date=date_obj,
                time=time,
                party_size=reservation_params.get("people", 2)
            )
            return {
                "available": is_available,
                "suggested_times": calendar.get_available_times(
                    date_obj,
                    reservation_params.get("people", 2)
                )
            }
        except Exception as e:
            return {"error": str(e)}
    
    tools = [check_availability]
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful restaurant reservation assistant.
        Current reservation details:
        - Date: {date}
        - Time: {time}
        - Number of people: {people}
        - Customer name: {name}
        
        Help the customer with their reservation request.
        Always be polite and professional.
        
        You have access to the following tools:
        - check_availability: Check if a table is available for a given date and time
        
        Use these tools to help customers make reservations."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Initialize memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # Create agent
    agent = create_openai_tools_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    
    # Create and return agent executor
    return AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True
    ) 