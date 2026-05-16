import asyncio
from app.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import nest_asyncio

# Allow nested event loops for testing in certain environments
nest_asyncio.apply()

async def run_test():
    print("🚀 Running Freelance Agent Test...")
    
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="app", user_id="user", session_id="s1")
    runner = Runner(agent=root_agent, app_name="app", session_service=session_service)
    
    # Requesting global remote jobs on HN
    message = types.Content(
        role="user", 
        parts=[types.Part.from_text(text="Zoek op Hacker News naar internationale Remote AI jobs. Schrijf een technisch diepgaand voorstel (in het Engels) voor een match.")]
    )
    
    print("\n🤖 Agent Response:")
    try:
        async for event in runner.run_async(
            user_id="user", 
            session_id="s1",
            new_message=message,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
    print("\n\n✅ Test Complete.")

if __name__ == "__main__":
    asyncio.run(run_test())
