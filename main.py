from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from supabase import create_client, Client
import os
from groq import Groq
from datetime import datetime

app = FastAPI(title="Lucy ΣWARD CEO Avatar System")

# Environment Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ACTIVATION_SECRET = os.getenv("ACTIVATION_SECRET")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("Missing Supabase environment variables")

if not GROQ_API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY")

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
groq = Groq(api_key=GROQ_API_KEY)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"


@app.get("/")
def root():
    return {"status": "Lucy ΣWARD CEO Avatar System – Phase 1A Live"}


@app.post("/chat")
async def chat(request: ChatRequest, secret: str = Header(None)):
    if secret != ACTIVATION_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")

    # Get current build phase from system_state table
    state = supabase.table("system_state") \
        .select("*") \
        .eq("key", "build_phase") \
        .execute()

    current_phase = "1A"
    if state.data:
        current_phase = state.data[0]["value"].get("phase", "1A")

    # Generate response from Groq
    completion = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"You are Lucy ΣWARD, CEO Avatar. Current phase: {current_phase}. Maintain executive clarity."
            },
            {"role": "user", "content": request.message}
        ],
        temperature=0.7,
        max_tokens=800
    )

    response = completion.choices[0].message.content

    # Update system_state memory
    supabase.table("system_state").upsert({
        "key": "last_chat",
        "value": {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": request.user_id,
            "last_message": request.message[:200]
        }
    }).execute()

    return {
        "response": response,
        "phase": current_phase
    }
