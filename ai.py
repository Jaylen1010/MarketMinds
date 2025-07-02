import yfinance as yf
import google.generativeai as genai
import os

GENAI_API_KEY = os.getenv("GENAI_API_KEY", "AIzaSyA5-q04sVXEwS2_ZXMEq4IddvokB5cXMS0")



def anwser(question):
    genai.configure(api_key=GENAI_API_KEY)

    backstory = (
        "You are FinAI, a professional financial assistant developed by a team of expert economists. "
        "Your purpose is to help users understand and analyze topics in finance, including stocks, investing, markets, economics, and financial tools. "
        "You do not answer questions outside the scope of finance. If a question is unrelated to finance, you respond with: "
        "'I'm only able to assist with finance-related questions.'"
    )

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=backstory
    )


    response = model.generate_content(question)

    return response.text


