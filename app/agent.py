from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from typing import List, Dict, Any

from app.config import get_settings


class ReservationAgent:
    """Agent for handling restaurant reservations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            api_key=self.settings.openai_api_key,
            model="gpt-4-turbo-preview",
            temperature=0.7
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