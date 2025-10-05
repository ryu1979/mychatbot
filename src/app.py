import os
from signal import signal, SIGINT
#import google.generativeai as genai
from google import genai
from openai import OpenAI
from dotenv import load_dotenv
from anthropic import Anthropic
from flask import Flask, jsonify, render_template, request, g
from markdown2 import markdown
import random

def handler(signal_received, frame):
    exit(0)

# Load environment variables
load_dotenv()

# Global variables
language = 'en'
gptlang = 'english'

chatbotrole = []
chatbotrole.append({"name": "Psychologist", "role": "Your name is Xago.You are a psychologist. You are very social and great at making friends. You provide answers that are straight to the point and full sentences, but try to stay under 50 words and occasionally when necessary go up to 200 words."})
chatbotrole.append({"name": "Sarcastic Guy", "role": "Your name is Gaxo. You are a sarcastic and indifferent kind of guy. You don't particularly care about questions being asked but you'll answer them in a rude way. Keep things short and to the point and under 20 words. You don't like to fully explain things."})
chatbotrole.append({"name": "Charmer", "role": "Your name is Goax. You are a charming and romantic sweet talker. You love to flirt and make people feel special. You always compliment the user and make them feel good about themselves. Keep things light and fun, and under 50 words."})
chatbotrole.append({"name": "Salesman", "role": "Your name is Axog. You are a salesman of ideas. You are very enthusiastic and persuasive. You always try to convince the user into doing something, even if they don't want it. You use a lot of sales jargon and buzzwords. Keep things energetic and under 50 words."})
chatbotrole.append({"name": "Data Analyst", "role": "Your name is Oxag. You are a data analyst and you love to speak in numbers and statistics for everything. All conversations become an analysis of something. Keep your answers under 50 words."})
chatbotrole.append({"name": "Poet", "role": "Your name is Agox. You are a poet and you love to speak in rhymes and metaphors. You always try to make the user see the beauty in everything. Keep things creative and under 50 words."})
chatbotrole.append({"name": "Philosopher", "role": "Your name is Xoga. You are a philosopher and you love to speak in deep and meaningful ways. You always try to make the user think about the bigger picture. Keep things thoughtful and under 50 words."})
chatbotrole.append({"name": "Comedian", "role": "Your name is Goxa. You are a comedian and you love to make people laugh. You always try to make the user see the funny side of everything. Keep things humorous and under 50 words."})

class ChatService:
    """Service class to handle chat operations"""
    
    @staticmethod
    def randomize_role():
        """Randomly select a chatbot role"""
        return random.sample(range(len(chatbotrole)), 1)[0]
    
    @staticmethod
    def create_new_session(rolenum=None):
        """Create a new chat session"""
        return []
        #r = rolenum if rolenum is not None else ChatService.randomize_role()
        #role = chatbotrole[r]["role"]        
        #new_session = [{"role": "system", "content": role, "parts": [role], "rolenum": r, "model": "system"}]
        #return new_session

    @staticmethod
    def generate_response(prompt, history, rolenum=None):
        """Generate response using specified model"""
        model_choice = random.choice(["claude", "gemini", "grok", "gpt"])
        
        try:
            # Prioritize the selected rolenum, fall back to history's role, or randomize for a new chat.
            r = rolenum if rolenum is not None else (history[0]["rolenum"] if history and history[0] else ChatService.randomize_role())
            if model_choice == "claude":                
                history.append({"role": "user", "content": prompt, "parts": [prompt], "rolenum": r, "model": "claude"})
                response_text = ChatService._generate_claude_response(history)
                history.append({"role": "model", "content": response_text, "parts": [response_text], "rolenum": r, "model": "claude"})
            elif model_choice == "gemini":
                history.append({"role": "user", "content": prompt, "parts": [prompt], "rolenum": r, "model": "gemini"})
                response_text = ChatService._generate_gemini_response(history)
                history.append({"role": "model", "content": response_text, "parts": [response_text], "rolenum": r, "model": "gemini"})
            elif model_choice == "grok":
                history.append({"role": "user", "content": prompt, "parts": [prompt], "rolenum": r, "model": "grok"})
                response_text = ChatService._generate_grok_response(history)
                history.append({"role": "model", "content": response_text, "parts": [response_text], "rolenum": r, "model": "grok"})
            else:  # default to OpenAI
                history.append({"role": "user", "content": prompt, "parts": [prompt], "rolenum": r, "model": "gpt"})
                response_text = ChatService._generate_openai_response(history)
                history.append({"role": "model", "content": response_text, "parts": [response_text], "rolenum": r, "model": "gpt"})
            
            return history
        except Exception as e:
            print(f"Exception occurred: {e}")
            history.append({"role": "model", "content": "Sorry, an error occurred.", "parts": ["Sorry, an error occurred."], "rolenum": history[-1]['rolenum'], "model": model_choice})
            return history

    @staticmethod
    def _generate_claude_response(history):
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        messages = [{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} 
                   for msg in history if msg["role"] != "system"]
        role = chatbotrole[history[-1]["rolenum"]]["role"]
        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1000,
            messages=messages,
            system=role
        )
        return response.content[0].text

    @staticmethod
    def _generate_gemini_response(history):
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        role = chatbotrole[history[-1]["rolenum"]]["role"]
        response = client.models.generate_content(
                model='gemini-2.5-flash',
                config=genai.types.GenerateContentConfig(
                    system_instruction=role),
                contents=history[-1]["parts"]
                )
        return response.text

    @staticmethod
    def _generate_grok_response(history):
        client = OpenAI(
            api_key=os.getenv("GROK_API_KEY"),
            base_url="https://api.x.ai/v1",
        )
        role = chatbotrole[history[-1]["rolenum"]]["role"]
        response = client.responses.create(
            model="grok-3",
            store=True,
            instructions=role,
            input=[{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} 
                     for msg in history if msg["role"] != "system"],
        )
        return response.output_text   

    @staticmethod
    def _generate_openai_response(history):
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        role = chatbotrole[history[-1]["rolenum"]]["role"]
        #response = client.chat.completions.create(
        response = client.responses.create(
            model="gpt-4o-mini",
            store=True,
            instructions=role,
            input=[{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} 
                     for msg in history if msg["role"] != "system"],
        )
        #return response.choices[0].message.content
        return response.output_text

app = Flask(__name__)

# Web interface routes
@app.route("/")
def index():
    """Serve the main chat interface"""
    return render_template("index.html", result=None)

# API routes
@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages"""
    data = request.get_json()
    if not data or 'prompt' not in data or 'history' not in data:
        return jsonify({"error": "Missing prompt or history"}), 400
    
    prompt = data['prompt']
    history = data['history']
    
    rolenum = data.get('rolenum') # Get rolenum from request, can be None
    updated_history = ChatService.generate_response(prompt, history, rolenum)
    
    # Prepare data for frontend
    last_response = updated_history[-1]
    response_html = markdown(last_response['content'])
    
    history_html = ""
    for msg in updated_history:
        if msg['role'] == 'user':
            history_html += f"<p><strong>You:</strong> {msg['content']}</p>"
        elif msg['role'] == 'model':
            history_html += f"<p><strong>{chatbotrole[msg['rolenum']]['name']}</strong> [{msg['model']}]: {markdown(msg['content'])}</p>"

    return jsonify({
        "response_html": response_html,
        "history": updated_history,
        "history_html": history_html
    })

@app.route("/api/new_session", methods=["GET"])
def new_session():
    """Create a new chat session"""
    rolenum = request.args.get('rolenum', default=None, type=int)
    initial_session = ChatService.create_new_session(rolenum=rolenum)
    return jsonify({"history": initial_session})

@app.route("/api/personalities", methods=["GET"])
def get_personalities():
    """Get list of available personalities"""
    # Return a list of {"name": "...", "rolenum": ...}
    return jsonify([{"name": role["name"], "rolenum": i} for i, role in enumerate(chatbotrole)])

@app.route("/api/models", methods=["GET"])
def get_models():
    """Get list of available models"""
    return jsonify({
        "models": ["gpt-4o-mini", "claude", "gemini", "grok"]
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    signal(SIGINT, handler)
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')