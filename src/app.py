import os

from signal import signal, SIGINT

import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
from anthropic import Anthropic

from flask import Flask, redirect, render_template, request, url_for

from markdown2 import markdown

def handler(signal_received, frame):
    # SIGINT or  ctrl-C detected, exit without error
    exit(0)

# Load environment variables from .env file
load_dotenv()
#from gtts import gTTS
language = 'en'
gptlang = 'english'
#session = {}
session = []

app = Flask(__name__)

@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        #animal = request.form["animal"]
        #place = request.form["place"]
        #person = request.form["person"]

        #prompt = "write a Children's Story in "+gptlang+" about a "+animal+" that goes to "+place+" and meets "+person

        prompt = request.form["prompt"]
        print(prompt)

        model = request.form["model"]

        if model == "gpt":
            client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
            #if model not in session:
            #    session[model] = []
            #session[model].append({"role": "user", "content": prompt})
            session.append({"role": "user", "content": prompt, "parts": [prompt]})
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    store=True,
                    messages=[msg for msg in session if msg["role"] == "user"]
                )
                mytext = response.choices[0].message.content
                session.append({"role": "model", "content": prompt, "parts": [mytext]})
            except Exception as e:
                print(f"Exception occurred: {e}")
                mytext = "Sorry, there was an error processing your request."

        elif model == "claude":
            client = Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
            try:
                response = client.messages.create(
                    model="claude-3-5-haiku-latest",
                    max_tokens=1000,
                    system="You are a world-class poet. Respond only with short poems.",
                    messages=[
                        {
                            "role": "user", 
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                )
                mytext = response.content
            except Exception as e:
                print(f"Exception occurred: {e}")
                mytext = "Sorry, there was an error processing your request."

        elif model == "gemini":            
            genai.configure(
                api_key=os.getenv("GEMINI_API_KEY")
            )
            m = genai.GenerativeModel('gemini-2.5-flash')
            #if model not in session:
            #    session[model] = []
            #session[model].append({"role": "user", "parts": [prompt]})
            session.append({"role": "user", "content": prompt, "parts": [prompt]})
            try:
                response = m.generate_content([{"role": msg["role"], "parts": msg["parts"]} for msg in session])
                mytext = response.text
                session.append({"role": "model", "content": mytext, "parts": [mytext]})
            except Exception as e:
                print(f"Exception occurred: {e}")
                mytext = "Sorry, there was an error processing your request."

        elif model == "grok":
            client = OpenAI(
                api_key=os.getenv("GROK_API_KEY"),
                base_url="https://api.x.ai/v1",
            )
            try:
                response = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.2,  # lower temperature for more deterministic answers
                )
                mytext = response.choices[0].message.content
            except Exception as e:
                print(f"Exception occurred: {e}")
                mytext = "Sorry, there was an error processing your request."
        
        print(mytext)
        mytext = markdown(mytext)
        #myobj = gTTS(text=mytext, lang=language, slow=False)
        #myobj.save("chatgpt.mp3")
        #os.system("chatgpt.mp3")
        return render_template("index.html", result=mytext, prompt=prompt)
    else:
        return render_template("index.html", result=None)

if __name__ == '__main__':
    signal(SIGINT, handler)
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
