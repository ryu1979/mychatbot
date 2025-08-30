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
session.append([])
current_session = []
current_session.append(session[-1])

app = Flask(__name__)

@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":

        model = request.form["model"]

        if model == "clear":
            if len(session[-1]) > 0:
                session.append([])
            current_session[0] = session[-1]
            print(f"there are {len(session)} sessions")
            return render_template("index.html", result=None)

        elif model.startswith("previous"):
            chatnum = int(model.replace('previous',''))
            print(f"{len(session)} sessions and trying to go back {chatnum} chats")
            if len(session) > chatnum:
                if(len(current_session[0])) == 0:
                    session[-1] = session.pop(-(chatnum+1))
                else:
                    session.append(session.pop(-(chatnum+1)))
                current_session[0] = session[-1]
                mytext = f"restoring to {chatnum} chats ago"
                mytext = markdown(mytext)
                print(f"loading {chatnum} chats ago")
            else:
                mytext = f"can't go back {chatnum} chats ago"
            history = ""
            for i in range(len(current_session[0])):
                history = f"""
                            {history}
                            {current_session[0][i]['role']}: {current_session[0][i]['parts'][0]}
                        """
            history = markdown(history)
            return render_template("index.html", result=mytext, history=history)

        else:
            prompt = request.form["prompt"]
            print(prompt)

            if model == "claude":
                client = Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                try:
                    current_session[0].append({"role": "user", "content": prompt, "parts": [prompt]})
                    messages = [{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} for msg in current_session[0]]
                    response = client.messages.create(
                        model="claude-3-5-haiku-latest",
                        max_tokens=100,
                        messages = messages
                    )
                    mytext = response.content[0].text
                    current_session[0].append({"role": "model", "content": mytext, "parts": [mytext]})
                except Exception as e:
                    print(f"Exception occurred: {e}")
                    mytext = "Sorry, there was an error processing your request."

            elif model == "gemini":            
                genai.configure(
                    api_key=os.getenv("GEMINI_API_KEY")
                )
                m = genai.GenerativeModel('gemini-2.5-flash')
                current_session[0].append({"role": "user", "content": prompt, "parts": [prompt]})
                try:
                    response = m.generate_content([{"role": msg["role"], "parts": msg["parts"]} for msg in current_session[0]])
                    mytext = response.text
                    current_session[0].append({"role": "model", "content": mytext, "parts": [mytext]})
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
            
            else:  # default to OpenAI
                client = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY")
                )
                try:
                    current_session[0].append({"role": "user", "content": prompt, "parts": [prompt]})
                except Exception as e:
                    print(f"Exception occurred: {e}")
                    mytext = "Sorry, there was an error processing your request."
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        store=True,
                        messages=[msg for msg in current_session[0] if msg["role"] == "user"]
                    )
                    mytext = response.choices[0].message.content
                    current_session[0].append({"role": "model", "content": prompt, "parts": [mytext]})
                except Exception as e:
                    print(f"Exception occurred: {e}")
                    mytext = "Sorry, there was an error processing your request."
            
            print(mytext)
            history = ""
            for i in range(len(current_session[0])):
                history = f"""
                            {history}
                            {current_session[0][i]['role']}: {current_session[0][i]['parts'][0]}
                        """
            mytext = markdown(mytext)
            history = markdown(history)

            return render_template("index.html", result=mytext, prompt=prompt, history=history)
    else:
        return render_template("index.html", result=None)

if __name__ == '__main__':
    signal(SIGINT, handler)
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
