from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import os
from groq import AsyncGroq  # Upgraded to the Async Engine

app = FastAPI(title="Maximus Cloud Core")

# Initialize Groq using the Async Engine to prevent server freezes
client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

base_prompt = {"role": "system", "content": "You are Maximus, a highly advanced AI. You operate with crisp, tactical efficiency. The year is 2026."}

async def analyze_task_complexity(user_query):
    """The micro-router to determine if the task needs the 70B heavy compute engine."""
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
    except Exception as e:
        print(f"[ROUTER ERROR]: {e}")
        return False

@app.get("/")
def health_check():
    return {"status": "Maximus Cloud Core Active", "intelligence": "Async Dual-Engine Linked"}

@app.websocket("/ws/command")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_messages = [base_prompt]
    
    while True:
        try:
            data = await websocket.receive_json()
            user_text = data.get("query", "")
            
            # MEMORY PRUNER
            if len(session_messages) > 11:
                session_messages = [session_messages[0]] + session_messages[-10:]
                
            session_messages.append({"role": "user", "content": user_text})
            
            # DUAL-ENGINE ROUTER
            is_heavy = await analyze_task_complexity(user_text)
            active_model = "llama-3.3-70b-versatile" if is_heavy else "llama-3.1-8b-instant"
            
            await websocket.send_json({"type": "status", "message": f"Engaging {active_model}..."})
            
            # ASYNC COGNITIVE STRIKE
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
            # If you close the app, Python drops the connection cleanly instead of crashing
            print("[SYSTEM] Client disconnected gracefully.")
            break
        except Exception as e:
            # If Groq fails, it sends the exact error back to your UI
            print(f"[FATAL ERROR]: {str(e)}")
            try:
                await websocket.send_json({"type": "error", "response": f"Matrix Error: {str(e)}"})
            except:
                break
