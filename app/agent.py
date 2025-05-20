from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain.tools import tool
from langchain.memory import ConversationBufferMemory
from typing import List, Dict, Any, Tuple
from datetime import datetime

from app.config import get_settings
from app.calendar import ReservationCalendar


class ReservationAgent:
    """Agent for handling restaurant reservations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            api_key=self.settings.openrouter_api_key,
            model="openai/gpt-4o",
            temperature=0.7,
            base_url="https://openrouter.ai/api/v1"
        )
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List:
        """Create tools for the agent."""
        @tool
        def check_availability(date: str, party_size: int) -> Dict[str, Any]:
            """Check table availability for a given date and party size."""
            # TODO: Implement actual availability checking logic
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
            # TODO: Implement actual reservation logic
            return {
                "success": True,
                "reservation_id": "12345",
                "confirmation_message": (
                    f"Reservation confirmed for {name} on {date} at {time}"
                )
            }
        
        return [check_availability, make_reservation]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the agent with tools and prompt."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful restaurant reservation assistant.
            Your goal is to help customers make reservations at the restaurant.
            Always be polite and professional.
            Ask for necessary information if it's missing."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True
        )
    
    async def process_message(
        self,
        message: str,
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """Process a message and return the agent's response."""
        if chat_history is None:
            chat_history = []
            
        response = await self.agent.ainvoke({
            "input": message,
            "chat_history": chat_history
        })
        
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
    
    # Initialize LLM with OpenRouter
    llm = ChatOpenAI(
        api_key=settings.openrouter_api_key,
        model="openai/gpt-4o",
        temperature=0.7,
        base_url="https://openrouter.ai/api/v1"
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
        ("system", """You are a helpful restaurant reservation assistant.\nCurrent reservation details:\n- Date: {date}\n- Time: {time}\n- Number of people: {people}\n- Customer name: {name}\nHelp the customer with their reservation request.\nAlways be polite and professional.\nIf you need to check availability, use the check_availability tool."""),
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
    agent = create_openai_functions_agent(
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