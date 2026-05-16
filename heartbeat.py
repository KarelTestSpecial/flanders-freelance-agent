import asyncio
import time
import os
import datetime
from app.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def run_heartbeat():
    print(f"💓 [{datetime.datetime.now()}] Freelance Heartbeat Started...")
    
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="app", user_id="system", session_id="heartbeat_session")
    runner = Runner(agent=root_agent, app_name="app", session_service=session_service)
    
    # Define the search mission
    mission = (
        "Scan ICTjob for 'AI', 'Python' and 'Solutions Architect' jobs in Gent or Remote. "
        "Scan Hacker News for 'Remote AI' roles. "
        "Save all found leads to the hub. "
        "If you find a role that perfectly matches the Athena CMS Factory (Sheet-to-site) profile, "
        "generate a high-priority pitch and flag it as 'DIAMOND'."
    )
    
    message = types.Content(
        role="user", 
        parts=[types.Part.from_text(text=mission)]
    )
    
    try:
        print("🤖 Agent is scanning the markets...")
        async for event in runner.run_async(
            user_id="system", 
            session_id="heartbeat_session",
            new_message=message,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        # Log activity to console
                        print(".", end="", flush=True)
        print("\n✅ Heartbeat cycle complete. Leads synced to Dashboard.")
    except Exception as e:
        print(f"\n❌ Heartbeat Error: {str(e)}")

async def main():
    # Run once immediately, then could be put in a loop
    # For this G.O.S. version, we run it once and let the user decide frequency
    await run_heartbeat()

if __name__ == "__main__":
    asyncio.run(main())
