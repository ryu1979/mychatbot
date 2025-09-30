import os
from signal import signal, SIGINT
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
from anthropic import Anthropic
from flask import Flask, jsonify, render_template, request
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
session = []
current_session = []

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
    def randomize_model():
        """Randomly select a llm model"""
        return random.sample(range(4), 1)[0]
    
    @staticmethod
    def create_new_session():
        """Create a new chat session"""
        # randomize the chatbot role
        r = ChatService.randomize_role()
        role = chatbotrole[r]["role"]

        newsession = [{"role": "system", "content": role, "parts": [role], "rolenum": r, "model": "system"}]
        
        new_session = [{"role": "system", "content": role, "parts": [role], "rolenum": r, "model": "system"}]
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                store=True,
                messages=newsession
                messages=new_session
            )
            mytext = response.choices[0].message.content
            newsession.append({"role": "model", "content": mytext, "parts": [mytext], "rolenum": r, "model": "gpt"})
            new_session.append({"role": "model", "content": mytext, "parts": [mytext], "rolenum": r, "model": "gpt"})
        except Exception as e:
            print(f"Exception occurred: {e}")
            mytext = "Sorry, there was an error processing your request."
            newsession.append({"role": "model", "content": mytext, "parts": [mytext], "rolenum": r, "model": "gpt"})
            new_session.append({"role": "model", "content": mytext, "parts": [mytext], "rolenum": r, "model": "gpt"})
            
        session.append(newsession)
        return newsession
        return new_session

    @staticmethod
    def restore_session(n_chats_ago):
        """Restore a previous session"""
        if len(current_session[0]) > 2:
            session.append(session.pop(-(n_chats_ago+1)))
        else:
            session[-1] = session.pop(-(n_chats_ago+1))
        return session[-1]

    @staticmethod
    def get_history():
        """Get chat history as formatted string"""
        history = ""
        for i in range(2, len(current_session[0])):
            if current_session[0][i]['role'] == 'user':
                history = f"""{history}
                        User: {current_session[0][i]['parts'][0]}
                    """
            else:
                history = f"""{history}
                           <p>{chatbotrole[current_session[0][i]['rolenum']]['name']}: [{current_session[0][i]['model']}] {current_session[0][i]['parts'][0]}</p>
                        """
        #print(markdown(history))
        return history

    @staticmethod
    def generate_response(prompt, model_name):
    def generate_response(prompt, history):
        """Generate response using specified model"""
        m = ChatService.randomize_model()

        model_choice = random.choice(["claude", "gemini", "grok", "gpt"])
        
        try:
            if m==1: #model_name == "claude":
            if model_choice == "claude":
                r = ChatService.randomize_role()
                current_session[0].append({"role": "user", "content": prompt, "parts": [prompt], "rolenum": r, "model": "claude"})
                return ChatService._generate_claude_response()
            elif m==2: #model_name == "gemini":
                r = current_session[0][0]["rolenum"]
                current_session[0].append({"role": "user", "content": prompt, "parts": [prompt], "rolenum": r, "model": "gemini"})
                return ChatService._generate_gemini_response()
            elif m==3: #model_name == "grok":
                r = current_session[0][0]["rolenum"]
                current_session[0].append({"role": "user", "content": prompt, "parts": [prompt], "rolenum": r, "model": "grok"})
                return ChatService._generate_grok_response()
                history.append({"role": "user", "content": prompt, "parts": [prompt], "rolenum": r, "model": "claude"})
                response_text = ChatService._generate_claude_response(history)
                history.append({"role": "model", "content": response_text, "parts": [response_text], "rolenum": r, "model": "claude"})
            elif model_choice == "gemini":
                r = history[0]["rolenum"]
                history.append({"role": "user", "content": prompt, "parts": [prompt], "rolenum": r, "model": "gemini"})
                response_text = ChatService._generate_gemini_response(history)
                history.append({"role": "model", "content": response_text, "parts": [response_text], "rolenum": r, "model": "gemini"})
            elif model_choice == "grok":
                r = history[0]["rolenum"]
                history.append({"role": "user", "content": prompt, "parts": [prompt], "rolenum": r, "model": "grok"})
                response_text = ChatService._generate_grok_response(history)
                history.append({"role": "model", "content": response_text, "parts": [response_text], "rolenum": r, "model": "grok"})
            else:  # default to OpenAI
                r = ChatService.randomize_role()
                current_session[0].append({"role": "user", "content": prompt, "parts": [prompt], "rolenum": r, "model": "gpt"})
                return ChatService._generate_openai_response()
                history.append({"role": "user", "content": prompt, "parts": [prompt], "rolenum": r, "model": "gpt"})
                response_text = ChatService._generate_openai_response(history)
                history.append({"role": "model", "content": response_text, "parts": [response_text], "rolenum": r, "model": "gpt"})
            
            return history
        except Exception as e:
            print(f"Exception occurred: {e}")
            return "Sorry, there was an error processing your request."
            history.append({"role": "model", "content": "Sorry, an error occurred.", "parts": ["Sorry, an error occurred."], "rolenum": history[-1]['rolenum'], "model": model_choice})
            return history

    @staticmethod
    def _generate_claude_response():
    def _generate_claude_response(history):
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        messages = [{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} 
                   for msg in current_session[0] if msg["role"] != "system"]
        role = chatbotrole[current_session[0][-1]["rolenum"]]["role"]
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
    def _generate_gemini_response():
    def _generate_gemini_response(history):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        m = genai.GenerativeModel('gemini-2.5-flash')
        response = m.generate_content([{"role": msg["role"], "parts": msg["parts"]} 
                                     for msg in current_session[0] if msg["role"] != "system"])
                                     for msg in history if msg["role"] != "system"])
        return response.text

    @staticmethod
    def _generate_grok_response():
    def _generate_grok_response(history):
        client = OpenAI(
            api_key=os.getenv("GROK_API_KEY"),
            base_url="https://api.x.ai/v1",
        )
        response = client.chat.completions.create(
            model="grok-3",
            messages=[{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} 
                     for msg in current_session[0]],
                     for msg in history],
            max_tokens=1000,
            temperature=0.2,
        )
        return response.choices[0].message.content

    @staticmethod
    def _generate_openai_response():
    def _generate_openai_response(history):
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        role = chatbotrole[current_session[0][-1]["rolenum"]]["role"]
        role = chatbotrole[history[-1]["rolenum"]]["role"]
        #response = client.chat.completions.create(
        response = client.responses.create(
            model="gpt-4o-mini",
            store=True,
            instructions=role,
            input=[{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} 
                     for msg in current_session[0] if msg["role"] != "system"],
                     for msg in history if msg["role"] != "system"],
        )
        #return response.choices[0].message.content
        return response.output_text

# Initialize first session
current_session.append(ChatService.create_new_session())

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
    if not data or 'prompt' not in data or 'model' not in data:
        return jsonify({"error": "Missing prompt or model"}), 400
    if not data or 'prompt' not in data or 'history' not in data:
        return jsonify({"error": "Missing prompt or history"}), 400
    
    prompt = data['prompt']
    model_name = data['model']
    history = data['history']
    
    response_text = ChatService.generate_response(prompt, model_name)
    r = current_session[0][-1]["rolenum"]
    m = current_session[0][-1]["model"]
    current_session[0].append({"role": "model", "content": response_text, "parts": [response_text], "rolenum": r, "model": m})
    updated_history = ChatService.generate_response(prompt, history)
    
    return jsonify({
        "response": response_text,
        "response_html": markdown(response_text),
        "history": ChatService.get_history(),
        "history_html": ChatService.get_history()
    })

@app.route("/api/sessions", methods=["POST"])
def create_session():
    """Create a new chat session"""
    if len(session[-1]) > 2:
        current_session[0] = ChatService.create_new_session()
    # Prepare data for frontend
    last_response = updated_history[-1]
    response_html = markdown(last_response['content'])
    
    return jsonify({
        "message": "New session created",
        "session_count": len(session)
    })
    history_html = ""
    for msg in updated_history:
        if msg['role'] == 'user':
            history_html += f"<p><strong>You:</strong> {msg['content']}</p>"
        elif msg['role'] == 'model':
            history_html += f"<p><strong>{chatbotrole[msg['rolenum']]['name']}</strong> [{msg['model']}]: {markdown(msg['content'])}</p>"

@app.route("/api/sessions/<int:chat_num>", methods=["PUT"])
def restore_session(chat_num):
    """Restore a previous session"""
    if len(session) > chat_num:
        current_session[0] = ChatService.restore_session(chat_num)
        message = f"Restored to {chat_num} chats ago"
        success = True
    else:
        message = f"Can't go back {chat_num} chats ago"
        success = False
    
    return jsonify({
        "success": success,
        "message": message,
        "history": ChatService.get_history(),
        "history_html": ChatService.get_history()
        "response_html": response_html,
        "history": updated_history,
        "history_html": history_html
    })

@app.route("/api/history", methods=["GET"])
def get_history():
    """Get current chat history"""
    return jsonify({
        "history": ChatService.get_history(),
        "history_html": ChatService.get_history(),
        "session_count": len(session)
    })
@app.route("/api/new_session", methods=["GET"])
def new_session():
    """Create a new chat session"""
    initial_session = ChatService.create_new_session()
    return jsonify({"history": initial_session})

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