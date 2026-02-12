from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from pydantic import BaseModel
import google.generativeai as genai  # <--- Using the library you currently have
import os
from dotenv import load_dotenv

# Import your existing routers and DB logic
from routes.user_routes import router as user_router
from routes.ai_response_routes import router as ai_response_router
from routes.email_routes import router as email_router
from routes.chat_routes import router as chat_router
from db import get_db, DATABASE_URL
from models import Base

# 1. Load Environment Variables
load_dotenv()

# 2. Configure Google Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("WARNING: GOOGLE_API_KEY not found in .env")

# Configure the old library
genai.configure(api_key=api_key)

app = FastAPI()

# 3. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Include your existing routers
app.include_router(user_router)
app.include_router(ai_response_router)
app.include_router(email_router)
app.include_router(chat_router)

# 5. Database Setup
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

# --- CHAT LOGIC ---

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_with_gemini(request: ChatRequest):
    if not api_key:
         raise HTTPException(status_code=500, detail="API Key missing. Check .env")

    # Retry logic for 429 errors & Model Fallback
    max_retries = 3
    base_delay = 2  # seconds
    
    # List of models to try in order of preference
    # 1.5-flash is standard for AI Studio keys
    # 2.0-flash is for newer/specific key types
    models_to_try = ['gemini-pro']
    
    current_model_index = 0

    for attempt in range(max_retries * len(models_to_try)):
        try:
            model_name = models_to_try[current_model_index]
            model = genai.GenerativeModel(model_name)
            
            # print(f"Attempting with model: {model_name}") # Debug log
            response = model.generate_content(request.message)
            
            if response.text:
                return {"response": response.text}
            else:
                return {"response": "I couldn't generate a response. Please try again."}
        
        except Exception as e:
            error_str = str(e)
            
            # Case 1: Model not found (404) -> Switch model immediately
            if "404" in error_str and "not found" in error_str:
                print(f"Model {model_name} not found. Switching to next model...")
                current_model_index += 1
                if current_model_index >= len(models_to_try):
                    raise HTTPException(status_code=500, detail="No compatible Gemini models found for your API key.")
                continue # Try next model immediately without delay

            # Case 2: Rate Limit (429) -> Wait and Retry same model
            elif "429" in error_str or "Resource has been exhausted" in error_str:
                if attempt < (max_retries * len(models_to_try)) - 1:
                    delay = base_delay * (2 ** (attempt % max_retries))
                    print(f"Rate limit exceeded on {model_name}. Retrying in {delay}s...")
                    import asyncio
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise HTTPException(status_code=429, detail="Gemini Rate Limit Exceeded. Please try again later.")
            
            # Case 3: Other errors
            else:
                print(f"Error with {model_name}: {e}")
                # If it's not a rate limit, maybe try the next model? 
                # For safety, let's switch model if we haven't exhausted them
                if current_model_index < len(models_to_try) - 1:
                     current_model_index += 1
                     continue
                
                raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

# --- End New Logic ---

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="[IP_ADDRESS]", port=8000, reload=True)