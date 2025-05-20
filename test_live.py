import asyncio
from app.agent import initialize_agent
from app.config import get_settings
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

async def test_reservation_flow():
    """Test the reservation agent with a series of sample conversations."""
    # Initialize reservation parameters
    reservation_params = {
        "date": "2024-03-20",
        "time": "19:00",
        "people": 4,
        "name": "John Doe"
    }
    
    # Initialize the agent
    agent = initialize_agent(reservation_params)
    
    # Sample conversation flow
    conversations = [
        "Hello, I'd like to make a reservation for tomorrow evening.",
        "Can you check if you have a table for 4 people at 7 PM?",
        "Yes, that works for me. Please book it under the name John Doe.",
        "Can you confirm my reservation details?",
    ]
    
    print("\n=== Starting Reservation Agent Test ===\n")
    
    for user_input in conversations:
        print(f"\nUser: {user_input}")
        
        try:
            response = await agent.ainvoke({
                "input": user_input,
                "date": reservation_params["date"],
                "time": reservation_params["time"],
                "people": reservation_params["people"],
                "name": reservation_params["name"]
            })
            
            print(f"Agent: {response['output']}")
            
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            break
        
        # Small delay between messages for better readability
        await asyncio.sleep(1)
    
    print("\n=== Test Completed ===\n")

if __name__ == "__main__":
    # Ensure OpenRouter API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("Error: OPENROUTER_API_KEY environment variable is not set")
        exit(1)
    
    # Run the test
    asyncio.run(test_reservation_flow()) 