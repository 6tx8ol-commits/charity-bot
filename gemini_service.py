import google.generativeai as genai

GEMINI_KEY = "AIzaSyCKN106cSz4SsFVJZHfLswYJWLKYwFEgbw"

genai.configure(api_key=GEMINI_KEY)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={
        "temperature": 0.7,
        "top_p": 0.95,
        "max_output_tokens": 1000,
    }
)

def ask_gemini(question):
    try:
        response = model.generate_content(question)
        return response.text
    except:
        return "عذراً، واجهت مشكلة حالياً."
