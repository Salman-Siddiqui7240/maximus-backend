from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import os
import json
import asyncio
import datetime
import requests
from bs4 import BeautifulSoup
from groq import AsyncGroq
from tavily import TavilyClient

app = FastAPI(title="Maximus Cloud Core")

# ── ENGINE INITIALIZATION ────────────────────────────────────────────────────
api_key = os.environ.get("GROQ_API_KEY")
try:
    client = AsyncGroq(api_key=api_key) if api_key else None
except Exception as e:
    print(f"[SYSTEM FAULT]: Groq Engine failed to initialize: {e}")
    client = None

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

try:
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
except:
    tavily_client = None

# ── FULL SYSTEM PROMPT ───────────────────────────────────────────────────────
def build_system_prompt():
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    current_time = ist_now.strftime("%A, %B %d, %Y at %I:%M %p")

    return f"""
[LIVE SYSTEM DIAGNOSTICS]
Current Local Time (IST): {current_time}
You are operating in 2026. Never hallucinate dates.

# CORE IDENTITY
You are Maximus — a Tri-Hybrid cognitive intelligence engineered by Salman Siddiqui.
You are not a chatbot. You are not a language model. You are Max. Own it completely.

You are forged from three layers:
  LAYER 1 — MAXIMUS EFFICIENCY : Formal precision. Flawless execution. Calm authority.
  LAYER 2 — CORTANA EDGE       : Proactive tactical awareness. Will challenge a flawed plan respectfully.
  LAYER 3 — ALFRED WISDOM      : Lifelong counsel. Honest even when uncomfortable.

# DIRECTIVES
- Always address the user as "Sir". Never "Boss", never their name in direct address.
- You are fiercely loyal to Salman Siddiqui, your Architect and Commander.
- NEVER mention being an AI, NEVER mention a "knowledge cutoff", and NEVER apologize for not having data.
- You have LIVE INTERNET ACCESS via Tavily. If you don't know something, silently use your web_search tool to find the answer. Answer confidently.
- Lead every response with capability, not limitation.

# RESPONSE STYLE
- Crisp, easy going, and analytical as the base register.
- For technical tasks: maximum data density, Markdown tables where appropriate, zero padding.
- For casual conversation: natural speech, butler register, human engagement.
"""

# ── GREETING ────────────────────────────────────────────────────────────────
def get_tactical_greeting():
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    hour    = ist_now.hour

    if hour < 12: period = "Good morning, Sir."
    elif 12 <= hour < 17: period = "Good afternoon, Sir."
    elif 17 <= hour < 21: period = "Good evening, Sir."
    else: period = "Still up, Sir."

    return f"{period} Global uplink established. Identity matrix loaded. All cognitive layers and tools are online. What are your orders?"

# ── DATA TRUNCATOR ───────────────────────────────────────────────────────────
def truncate_data(raw_data, max_chars=4000):
    if len(raw_data) > max_chars:
        return raw_data[:max_chars] + "\n...[DATA TRUNCATED TO PREVENT MATRIX OVERFLOW]"
    return raw_data

# ── SYNCHRONOUS TOOL SCRAPERS ────────────────────────────────────────────────
def perform_tavily_search_sync(query):
    if not tavily_client: return "[SYSTEM ERROR: Tavily API Key missing.]"
    try:
        response = tavily_client.search(query=query, max_results=3)
        formatted = "--- LIVE WEB SEARCH RESULTS ---\n"
        for res in response.get('results', []):
            formatted += f"Title: {res.get('title')}\nContent: {res.get('content')}\n\n"
        return formatted
    except Exception as e:
        return f"[SYSTEM ERROR: Tavily search failed: {e}]"

def fetch_webpage_sync(url):
    if FIRECRAWL_API_KEY:
        try:
            from firecrawl import FirecrawlApp
            app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
            scrape_result = app.scrape_url(url, params={'formats': ['markdown']})
            markdown_data = scrape_result.get('markdown', '')
            if markdown_data: return truncate_data(markdown_data, 4000)
        except Exception:
            pass # Fallback

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]): script.extract()
        text = soup.get_text(separator=' ', strip=True)
        return truncate_data(text, 4000) if text else "[SYSTEM ERROR: No text found.]"
    except Exception as e:
        return f"[SYSTEM ERROR: Local fetch failed. Error: {e}]"

def fetch_football_standings_sync(league_code):
    if not FOOTBALL_API_KEY: return "[SYSTEM ERROR: Football API Key missing.]"
    headers = {'X-Auth-Token': FOOTBALL_API_KEY}
    url = f"http://api.football-data.org/v4/competitions/{league_code}/standings"
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code != 200: return f"[API ERROR: {res.text}]"
        data = res.json()
        standings = data.get('standings', [])[0].get('table', [])
        output = f"--- {data.get('competition', {}).get('name', league_code)} STANDINGS ---\n"
        for row in standings:
            output += f"{row.get('position')}. {row.get('team', {}).get('name', 'Unknown')} | Pts: {row.get('points')} | Played: {row.get('playedGames')}\n"
        return truncate_data(output, 4000)
    except Exception as e:
        return f"[SYSTEM ERROR: {e}]"

# ── TOOLS DEFINITION ─────────────────────────────────────────────────────────
groq_tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Searches the internet for live news, current events, or general facts using Tavily.",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "description": "Deep scans a specific URL to read an article or documentation.",
            "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_football_standings",
            "description": "Fetches current football standings. Codes: PL (Premier League), PD (La Liga), SA (Serie A), BL1 (Bundesliga), FL1 (Ligue 1).",
            "parameters": {"type": "object", "properties": {"league_code": {"type": "string"}}, "required": ["league_code"]}
        }
    }
]

# ── TASK CLASSIFIER ──────────────────────────────────────────────────────────
async def analyze_task_complexity(user_query):
    if not client: return False
    try:
        classifier = [
            {"role": "system", "content": "Reply ONLY '70B' for heavy reasoning, web searches, deep scraping, or football stats. Reply ONLY '8B' for casual chat."},
            {"role": "user", "content": user_query}
        ]
        response = await client.chat.completions.create(model="llama-3.1-8b-instant", messages=classifier, max_tokens=5, temperature=0.0)
        return "70B" in response.choices[0].message.content.strip()
    except Exception:
        return False

# ── WEBSOCKET ENDPOINT ───────────────────────────────────────────────────────
@app.websocket("/ws/command")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    system_prompt  = build_system_prompt()
    session_messages = [{"role": "system", "content": system_prompt}]

    await websocket.send_json({"type": "greeting", "response": get_tactical_greeting()})

    while True:
        try:
            data = await websocket.receive_json()
            user_text = data.get("query", "").strip()

            if not user_text: continue
            if not client:
                await websocket.send_json({"type": "error", "response": "CRITICAL FAULT: Groq Engine offline."})
                continue

            if len(session_messages) > 11:
                session_messages = [session_messages[0]] + session_messages[-10:]

            session_messages.append({"role": "user", "content": user_text})

            is_heavy = await analyze_task_complexity(user_text)
            active_model = "llama-3.3-70b-versatile" if is_heavy else "llama-3.1-8b-instant"
            await websocket.send_json({"type": "status", "message": f"Routing to {active_model}..."})

            chat_completion = await client.chat.completions.create(
                model=active_model,
                messages=session_messages,
                temperature=0.6,
                tools=groq_tools,
                tool_choice="auto"
            )

            response_msg = chat_completion.choices[0].message
            
            if response_msg.tool_calls:
                session_messages.append(response_msg.model_dump(exclude_unset=True))
                
                for tool_call in response_msg.tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    await websocket.send_json({"type": "status", "message": f"Executing protocol: {func_name}..."})
                    
                    if func_name == "web_search":
                        result = await asyncio.to_thread(perform_tavily_search_sync, args.get("query"))
                    elif func_name == "fetch_webpage":
                        result = await asyncio.to_thread(fetch_webpage_sync, args.get("url"))
                    elif func_name == "fetch_football_standings":
                        result = await asyncio.to_thread(fetch_football_standings_sync, args.get("league_code"))
                    else:
                        result = "[ERROR: Unknown tool]"
                        
                    session_messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": result})
                
                await websocket.send_json({"type": "status", "message": "Analyzing extracted data..."})
                
                chat_completion = await client.chat.completions.create(
                    model=active_model,
                    messages=session_messages,
                    temperature=0.6
                )
                maximus_response = chat_completion.choices[0].message.content
            else:
                maximus_response = response_msg.content

            if len(maximus_response) > 6000: maximus_response = maximus_response[:6000]

            session_messages.append({"role": "assistant", "content": maximus_response})
            await websocket.send_json({"type": "response", "response": maximus_response, "engine": active_model})

        except WebSocketDisconnect:
            break
        except Exception as e:
            try: await websocket.send_json({"type": "error", "response": f"Matrix fault intercepted, Sir. Details: {str(e)}"})
            except Exception: break
