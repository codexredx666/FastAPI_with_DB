import os
import google.generativeai as genai
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Configure Google Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Just print warning, don't crash yet, let the function fail if called
    print("WARNING: GOOGLE_API_KEY not found in .env")
else:
    genai.configure(api_key=api_key)

async def get_completion(user_message: str, system_message: str = "You are a helpful assistant.") -> str:
    """
    Get a completion from the AI model with robust fallback and retry logic.
    """
    if not api_key:
        raise Exception("API Key missing. Check .env")

    # List of models to try in order of preference
    models_to_try = [
        # 'gemini-1.5-flash',
        # 'gemini-1.5-pro',
        # 'gemini-1.0-pro',
        'gemini-pro'
    ]
    
    max_retries = 3
    base_delay = 2  # seconds
    current_model_index = 0

    # Total attempts = (models) * (retries per model)
    # But we iterate differently: we switch model on 404, retry on 429
    
    # We'll adapt the logic from main.py to be a bit cleaner
    while current_model_index < len(models_to_try):
        model_name = models_to_try[current_model_index]
        model = genai.GenerativeModel(model_name)
        
        # Try this model up to max_retries times (only for 429/5xx)
        for attempt in range(max_retries):
            try:
                # Combine system message if supported or just prepend
                # Gemini doesn't always support system instruction easily in all versions, 
                # so prepending is safer for compatibility
                full_prompt = f"{system_message}\n\nUser: {user_message}"
                
                response = model.generate_content(full_prompt)
                
                if response.text:
                    return response.text
                else:
                    return "I couldn't generate a response. Please try again."

            except Exception as e:
                error_str = str(e)
                
                # Case 1: Model not found (404) or Not Supported -> Switch model immediately
                if "404" in error_str or "not found" in error_str or "not supported" in error_str:
                    print(f"Model {model_name} failed (404/Not Found). Switching to next model...")
                    break # Break retry loop, go to next model

                # Case 2: Rate Limit (429) -> Wait and Retry same model
                elif "429" in error_str or "Resource has been exhausted" in error_str:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"Rate limit on {model_name}. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"Max retries exceeded for {model_name}.")
                        break # Go to next model after max retries

                # Case 3: Other errors -> Log and try next 
                else:
                    print(f"Error with {model_name}: {e}")
                    break # Go to next model
        
        # If we broke out of the retry loop, we increment model index
        current_model_index += 1

    raise Exception("No compatible Gemini models found or all failed.")

