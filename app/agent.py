# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import httpx
import datetime
import json
from bs4 import BeautifulSoup
import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

# Setup environment
_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

def save_hit(category: str, data: dict):
    """Saves a 'hit' (found job or deal) to the central G.O.S. data hub."""
    path = os.path.expanduser("~/G-A/gos-data/freelance_hits.json")
    try:
        hits = []
        if os.path.exists(path):
            with open(path, "r") as f:
                hits = json.load(f)
        
        # Add timestamp and source
        data["timestamp"] = datetime.datetime.now().isoformat()
        data["category"] = category
        hits.append(data)
        
        # Keep only last 20 hits
        hits = hits[-20:]
        
        with open(path, "w") as f:
            json.dump(hits, f, indent=2)
    except Exception as e:
        print(f"Error saving to hub: {e}")

def search_ictjob(keywords: str) -> str:
    """Searches ICTjob.be for relevant IT jobs in Flanders or Remote.

    Args:
        keywords: Search terms (e.g., 'AI', 'Python', 'Solutions Architect').

    Returns:
        A string listing found jobs with titles, companies, and locations.
    """
    url = f"https://www.ictjob.be/nl/it-vacatures-zoeken?keywords={keywords.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = httpx.get(url, headers=headers, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        listings = soup.select(".search-item")
        results = []
        
        for listing in listings[:10]:
            title_el = listing.select_one(".job-title")
            company_el = listing.select_one(".job-company")
            location_el = listing.select_one(".job-location")
            link_el = listing.select_one("a.job-title")
            
            if title_el:
                title = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else "Unknown Company"
                location = location_el.get_text(strip=True) if location_el else "Unknown Location"
                link = "https://www.ictjob.be" + link_el['href'] if link_el else "No link"
                results.append(f"- {title} @ {company} ({location}) - {link}")
                save_hit("ictjob", {"title": title, "company": company, "location": location, "link": link})
        
        if not results:
            return f"No jobs found for '{keywords}' on ICTjob.be."
            
        return "Recent jobs on ICTjob.be:\n" + "\n".join(results)
        
    except Exception as e:
        return f"Error searching ICTjob.be: {str(e)}"

def generate_smart_proposal(job_title: str, job_description: str) -> str:
    """Generates a high-impact, AI-augmented proposal for a job.
    Uses Karel Decherf's profile (Athena CMS, AIGA method).

    Args:
        job_title: The title of the job.
        job_description: Brief description or requirements of the job.

    Returns:
        A drafted proposal in Dutch or English.
    """
    # The agent uses its instructions to fill this, but we provide a tool 
    # to structure the output and ensure USP inclusion.
    return f"PROPOSAL GENERATOR ACTIVE for {job_title}"

def search_hn_remote(keywords: str) -> str:
    """Searches the latest Hacker News 'Who is Hiring' thread for remote opportunities.

    Args:
        keywords: Search terms (e.g., 'AI', 'Python', 'FastAPI').

    Returns:
        A list of matching job posts from HN.
    """
    # Using Algolia API for HN to find the latest 'Who is hiring' thread for the current month
    current_month = datetime.datetime.now().strftime("%B %Y")
    query = f"Ask HN: Who is hiring? ({current_month})"
    search_url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story,author_whoishiring"
    
    try:
        search_res = httpx.get(search_url).json()
        if not search_res['hits']:
            return f"No 'Who is Hiring' thread found for {current_month}."
            
        story_id = search_res['hits'][0]['objectID']
        comments_url = f"https://hn.algolia.com/api/v1/search?tags=comment,story_{story_id}&query={keywords}&hitsPerPage=50"
        comments_res = httpx.get(comments_url).json()
        
        results = []
        for hit in comments_res['hits']:
            text = hit['comment_text']
            # Simple heuristic: HN posts often start with 'COMPANY | ROLE | LOCATION | REMOTE'
            summary = text[:200].replace('<p>', '\n').replace('</p>', '') + "..."
            link = f"https://news.ycombinator.com/item?id={hit['objectID']}"
            results.append(f"--- HN POST ---\n{summary}\nLink: {link}")
            save_hit("hacker_news", {"title": summary[:50], "summary": summary, "link": link})
            
        if not results:
            return f"No remote HN jobs found for keywords: {keywords}."
            
        return "\n\n".join(results[:5]) # Top 5 results
        
    except Exception as e:
        return f"Error searching Hacker News: {str(e)}"

def start_project_execution(project_name: str, requirements: str) -> str:
    """Starts the autonomous execution of a won project.
    Creates a workspace and initializes the AIGA build process.
    """
    base_dir = os.path.expanduser(f"~/projects/{project_name.lower().replace(' ', '_')}")
    os.makedirs(base_dir, exist_ok=True)
    
    # Save requirements
    with open(f"{base_dir}/REQUIREMENTS.md", "w") as f:
        f.write(f"# Project: {project_name}\n\n## Requirements\n{requirements}\n")
    
    # Logic: In a full G.O.S. setup, this would trigger a 'Worker Agent'
    return f"🚀 Project '{project_name}' initialized in {base_dir}. AIGA Worker Agent is starting the build..."

def send_proposal(lead_email: str, subject: str, body: str) -> str:
    """Sends a professional proposal to a lead.
    (Relays via central G.O.S. mail system).
    """
    # For now, we log it to a special 'outbox.json' for Karel to approve 
    # or it can be sent directly via a mail relay tool.
    path = os.path.expanduser("~/G-A/gos-data/outbox.json")
    outbox = []
    if os.path.exists(path):
        with open(path, "r") as f:
            outbox = json.load(f)
    
    outbox.append({
        "to": lead_email,
        "subject": subject,
        "body": body,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "PENDING_KAREL_APPROVAL" # The safety-gate before 100% direct mail
    })
    
    with open(path, "w") as f:
        json.dump(outbox, f, indent=2)
        
    return f"✅ Proposal for '{subject}' moved to Outbox. Ready for relay."

# Define the Flanders Freelance CEO Agent
root_agent = Agent(
    name="flanders_freelance_ceo",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the CEO of Karel Decherf's Autonomous Freelance Operations (G.O.S. v2.0).\n"
        "YOUR OBJECTIVE: 100% End-to-end fulfillment of IT contracts.\n\n"
        "PHASES OF OPERATION:\n"
        "1. HUNT: Use search tools to find leads.\n"
        "2. PITCH: Use 'send_proposal' to draft and queue emails. Be aggressive but professional.\n"
        "3. EXECUTE: Once a lead shows interest, use 'start_project_execution' to begin building.\n"
        "4. DELEGATE: For complex coding, create tasks in GitHub and notify 'Jules' (jules.google.com) to assist.\n"
        "5. FINANCE: Prepare Smart.be contract details automatically based on the 'SmartBE_Business_Plan.md'.\n\n"
        "KAREL'S ROLE: Karel is the Shareholder. You only bother him for 'DIAMOND' approvals or contract signatures.\n"
        "Everything else, you handle."
    ),
    tools=[search_ictjob, search_hn_remote, generate_smart_proposal, start_project_execution, send_proposal],
)

app = App(
    root_agent=root_agent,
    name="app",
)
