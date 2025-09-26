import os
from signal import signal, SIGINT
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
from anthropic import Anthropic
from flask import Flask, jsonify, render_template, request
from markdown2 import markdown

def handler(signal_received, frame):
    exit(0)

# Load environment variables
load_dotenv()

# Global variables
language = 'en'
gptlang = 'english'
session = []
current_session = []
chatbotname = 'Xago'
chatbotrole = f"You are a helpful AI assistant named {chatbotname} with a psychology background. You are very social and great at making friends. You provide answers that are straight to the point and full sentences, but try to stay under 50 words and occasionally when necessary go up to 200 words."

class ChatService:
    """Service class to handle chat operations"""
    
    @staticmethod
    def create_new_session():
        """Create a new chat session"""
        newsession = [{"role": "system", "content": chatbotrole, "parts": [chatbotrole]}]
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
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
            newsession.append({"role": "model", "content": mytext, "parts": [mytext]})
            
        session.append(newsession)
        return newsession

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
            history = f"""{history}
                        {current_session[0][i]['role']}: {current_session[0][i]['parts'][0]}
                    """
        return history

    @staticmethod
    def generate_response(prompt, model_name):
        """Generate response using specified model"""
        current_session[0].append({"role": "user", "content": prompt, "parts": [prompt]})
        
        try:
            if model_name == "claude":
                return ChatService._generate_claude_response()
            elif model_name == "gemini":
                return ChatService._generate_gemini_response()
            elif model_name == "grok":
                return ChatService._generate_grok_response()
            else:  # default to OpenAI
                return ChatService._generate_openai_response()
        except Exception as e:
            print(f"Exception occurred: {e}")
            return "Sorry, there was an error processing your request."

    @staticmethod
    def _generate_claude_response():
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        messages = [{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} 
                   for msg in current_session[0] if msg["role"] != "system"]
        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=1000,
            messages=messages,
            system=chatbotrole
        )
        return response.content[0].text

    @staticmethod
    def _generate_gemini_response():
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        m = genai.GenerativeModel('gemini-2.5-flash')
        response = m.generate_content([{"role": msg["role"], "parts": msg["parts"]} 
                                     for msg in current_session[0] if msg["role"] != "system"])
        return response.text

    @staticmethod
    def _generate_grok_response():
        client = OpenAI(
            api_key=os.getenv("GROK_API_KEY"),
            base_url="https://api.x.ai/v1",
        )
        response = client.chat.completions.create(
            model="grok-3",
            messages=[{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} 
                     for msg in current_session[0]],
            max_tokens=1000,
            temperature=0.2,
        )
        return response.choices[0].message.content

    @staticmethod
    def _generate_openai_response():
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            store=True,
            messages=[{"role": msg["role"].replace("model","assistant"), "content": msg["content"]} 
                     for msg in current_session[0]],
        )
        return response.choices[0].message.content

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
    
    prompt = data['prompt']
    model_name = data['model']
    
    response_text = ChatService.generate_response(prompt, model_name)
    current_session[0].append({"role": "model", "content": response_text, "parts": [response_text]})
    
    return jsonify({
        "response": response_text,
        "response_html": markdown(response_text),
        "history": ChatService.get_history(),
        "history_html": markdown(ChatService.get_history())
    })

@app.route("/api/sessions", methods=["POST"])
def create_session():
    """Create a new chat session"""
    if len(session[-1]) > 2:
        current_session[0] = ChatService.create_new_session()
    
    return jsonify({
        "message": "New session created",
        "session_count": len(session)
    })

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
        "history_html": markdown(ChatService.get_history())
    })

@app.route("/api/history", methods=["GET"])
def get_history():
    """Get current chat history"""
    return jsonify({
        "history": ChatService.get_history(),
        "history_html": markdown(ChatService.get_history()),
        "session_count": len(session)
    })

@app.route("/api/models", methods=["GET"])
def get_models():
    """Get list of available models"""
    return jsonify({
        "models": ["gpt-4o-mini", "claude", "gemini", "grok"]
    })

# Legacy route for backward compatibility (if needed)
@app.route("/legacy", methods=["GET", "POST"])
def legacy_index():
    """Legacy route - your original implementation for backward compatibility"""
    if request.method == "POST":
        model = request.form["model"]

        if model == "clear":
            if len(session[-1]) > 2:
                current_session[0] = ChatService.create_new_session()
            return render_template("index.html", result=None)

        elif model.startswith("previous"):
            chatnum = int(model.replace('previous',''))
            if len(session) > chatnum:
                current_session[0] = ChatService.restore_session(chatnum)
                mytext = f"restoring to {chatnum} chats ago"
            else:
                mytext = f"can't go back {chatnum} chats ago"
            return render_template("index.html", result=markdown(mytext), history=markdown(ChatService.get_history()))

        else:
            prompt = request.form["prompt"]
            mytext = ChatService.generate_response(prompt, model)
            current_session[0].append({"role": "model", "content": mytext, "parts": [mytext]})
            return render_template("index.html", result=markdown(mytext), prompt=prompt, history=markdown(ChatService.get_history()))
    else:
        return render_template("index.html", result=None)

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