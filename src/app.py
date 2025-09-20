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

session = []
current_session = []

chatbotname = 'Xago'
chatbotrole = f"You are a helpful AI assistant named {chatbotname} with a psychology background. You are very social and great at making friends. You provide answers that are straight to the point and full sentences, but try to stay under 50 words and occasionally when necessary go up to 200 words."

def getnewsession():
    newsession = [{"role": "system", "content": chatbotrole, "parts": [chatbotrole]}]
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            store=True,
            messages=newsession
        )
        mytext = response.choices[0].message.content
        newsession.append({"role": "model", "content": mytext, "parts": [mytext]})
    except Exception as e:
        print(f"Exception occurred: {e}")
        mytext = "Sorry, there was an error processing your request."
    session.append(newsession)
    return newsession

def restoresession(n_chats_ago):
    if(len(current_session[0])) > 2:
        session.append(session.pop(-(n_chats_ago+1)))
    else:
        session[-1] = session.pop(-(n_chats_ago+1))
    return session[-1]

def gethistory():
    history = ""
    for i in range(2,len(current_session[0])):
        history = f"""
                    {history}
                    {current_session[0][i]['role']}: {current_session[0][i]['parts'][0]}
                """
    return history

current_session.append(getnewsession())
print(current_session)

app = Flask(__name__)

@app.route("/", methods=("GET", "POST"))
def index():    
    if request.method == "POST":

        model = request.form["model"]

        if model == "clear":
            if len(session[-1]) > 2:
                current_session[0] = getnewsession()
            print(f"there are {len(session)} sessions")
            return render_template("index.html", result=None)

        elif model.startswith("previous"):
            chatnum = int(model.replace('previous',''))
            print(f"{len(session)} sessions and trying to go back {chatnum} chats")
            if len(session) > chatnum:
                current_session[0] = restoresession(chatnum)
                mytext = f"restoring to {chatnum} chats ago"
            else:
                mytext = f"can't go back {chatnum} chats ago"
            return render_template("index.html", result=markdown(mytext), history=markdown(gethistory()))

        else:
            prompt = request.form["prompt"]
            current_session[0].append({"role": "user", "content": prompt, "parts": [prompt]})
            print(current_session)
            
            if model == "claude":
                client = Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                try:
                    messages = [{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} for msg in current_session[0] if msg["role"] != "system"]
                    response = client.messages.create(
                        model="claude-3-5-haiku-latest",
                        max_tokens=1000,
                        messages = messages,
                        system = chatbotrole
                    )
                    mytext = response.content[0].text
                except Exception as e:
                    print(f"Exception occurred: {e}")
                    mytext = "Sorry, there was an error processing your request."

            elif model == "gemini":            
                genai.configure(
                    api_key=os.getenv("GEMINI_API_KEY")
                )
                m = genai.GenerativeModel('gemini-2.5-flash')
                try:
                    response = m.generate_content([{"role": msg["role"], "parts": msg["parts"]} for msg in current_session[0] if msg["role"] != "system"])
                    mytext = response.text
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
                        messages = [{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} for msg in current_session[0]],
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
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        store=True,
                        messages = [{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} for msg in current_session[0]],
                    )
                    mytext = response.choices[0].message.content
                except Exception as e:
                    print(f"Exception occurred: {e}")
                    mytext = "Sorry, there was an error processing your request."
            
            current_session[0].append({"role": "model", "content": mytext, "parts": [mytext]})
            print(mytext)

            return render_template("index.html", result=markdown(mytext), prompt=prompt, history=markdown(gethistory()))
    else:
        return render_template("index.html", result=None)

if __name__ == '__main__':
    signal(SIGINT, handler)
    server_port = os.environ.get('PORT', '5000')
    app.run(debug=False, port=server_port, host='0.0.0.0')
