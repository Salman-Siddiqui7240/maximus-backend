from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import os
import datetime
from groq import AsyncGroq

app = FastAPI(title="Maximus Cloud Core")

# --- ARMORED ENGINE INITIALIZATION ---
# This prevents the server from detonating if the API key is missing or corrupted.
api_key = os.environ.get("GROQ_API_KEY")
try:
    client = AsyncGroq(api_key=api_key) if api_key else None
except Exception as e:
    print(f"[SYSTEM FAULT]: Groq Engine failed to initialize: {e}")
    client = None

base_prompt = {"role": "system", "content": "You are Maximus, a highly advanced AI. You operate with crisp, tactical efficiency. You must always address the user as Sir. The year is 2026."}

def get_tactical_greeting():
    """Restores the dynamic personality module based on standard IST (UTC+5:30)."""
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    hour = ist_now.hour

    if hour < 12:
        greet = "Good morning, Sir."
    elif 12 <= hour < 18:
        greet = "Good afternoon, Sir."
    else:
        greet = "Good evening, Sir."
        
    return f"{greet} Global uplink established. Identity matrix online. What are your orders?"

async def analyze_task_complexity(user_query):
    if not client: return False
    try:
        classifier = [
            {"role": "system", "content": "Output ONLY '8B' for casual conversation. Output '70B' for complex logic or coding."},
            {"role": "user", "content": user_query}
        ]
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=classifier,
            max_tokens=5,
            temperature=0.0
        )
        return "70B" in response.choices[0].message.content.strip()
    except Exception:
        return False

@app.get("/")
def health_check():
    return {"status": "Maximus Cloud Core Active", "brain_status": "ONLINE" if client else "OFFLINE"}

@app.websocket("/ws/command")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_messages = [base_prompt]
    
    # 1. PUSH THE DYNAMIC PERSONALITY GREETING TO THE UI IMMEDIATELY
    await websocket.send_json({"type": "greeting", "response": get_tactical_greeting()})
    
    while True:
        try:
            data = await websocket.receive_json()
            user_text = data.get("query", "")
            
            # 2. FAIL-SAFE: Check if the brain is missing BEFORE trying to process
            if not client:
                await websocket.send_json({"type": "error", "response": "CRITICAL FAULT: Groq Engine offline. Check Render Environment Vault."})
                continue
            
            # MEMORY PRUNER
            if len(session_messages) > 11:
                session_messages = [session_messages[0]] + session_messages[-10:]
                
            session_messages.append({"role": "user", "content": user_text})
            
            # DUAL-ENGINE ROUTER
            is_heavy = await analyze_task_complexity(user_text)
            active_model = "llama-3.3-70b-versatile" if is_heavy else "llama-3.1-8b-instant"
            
            await websocket.send_json({"type": "status", "message": f"Engaging {active_model}..."})
            
            # COGNITIVE STRIKE
            chat_completion = await client.chat.completions.create(
                model=active_model,
                messages=session_messages
            )
            
            maximus_response = chat_completion.choices[0].message.content
            session_messages.append({"role": "assistant", "content": maximus_response})
            
            await websocket.send_json({
                "type": "response",
                "response": maximus_response,
                "engine": active_model
            })
            
        except WebSocketDisconnect:
            print("[SYSTEM] Client severed connection.")
            break
        except Exception as e:
            # Absolute Error Catching
            print(f"[FATAL ERROR]: {str(e)}")
            try:
                await websocket.send_json({"type": "error", "response": f"Matrix Fault: {str(e)}"})
            except:
                break
