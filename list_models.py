import google.generativeai as genai

api_key = "AIzaSyDgEJBfT80GmjQPfOgTUlQHJqOEyuu5jIY"
genai.configure(api_key=api_key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
