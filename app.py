from flask import Flask, render_template, jsonify, redirect, url_for
import os
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/status')
def status():
    return render_template('status.html')

@app.route('/api/status')
def api_status():
    return jsonify({
        "status": "online",
        "message": "JoeA Discord Bot is running",
        "timestamp": datetime.datetime.now().isoformat(),
        "services": {
            "bot": "online",
            "web": "online",
            "database": "online",
            "ai": "online"
        }
    })

@app.route('/commands')
def command_list():
    general_commands = [
        {"name": "!register [info]", "description": "Register yourself with the bot with optional additional information"},
        {"name": "!chat [message]", "description": "Start a conversation with the AI"},
        {"name": "!news", "description": "Get information about an important world event today"},
        {"name": "!tdih", "description": "Shows a historical event that happened on this day"},
        {"name": "!calc [expression]", "description": "Calculate mathematical expressions"},
        {"name": "!weather [city]", "description": "Get current weather for any city"},
        {"name": "!translate [language] [text]", "description": "Translate text to another language"},
        {"name": "!fact", "description": "Get an interesting random fact"},
        {"name": "!profile", "description": "View your profile information"},
        {"name": "!info", "description": "List all registered users"},
        {"name": "!commands", "description": "Show all available commands"},
        {"name": "!serverinfo", "description": "Display detailed information about the server"}
    ]
    
    moderation_commands = [
        {"name": "!ban [user_id] [reason]", "description": "Ban a user from the server (requires ban permission)"},
        {"name": "!unban [user_id]", "description": "Remove a ban from a user (requires ban permission)"},
        {"name": "!kick [user] [reason]", "description": "Kick a user from the server (requires kick permission)"},
        {"name": "!slowmode [seconds]", "description": "Set slowmode delay for the channel (requires manage channels)"},
        {"name": "!rerole [user] [role]", "description": "Remove a specific role from a user (requires manage roles)"},
        {"name": "!role [user] [role]", "description": "Add or remove roles from a user (requires manage roles)"},
        {"name": "!clear [amount]", "description": "Delete recent messages (requires manage messages)"}
    ]
    
    return render_template('commands.html', general_commands=general_commands, moderation_commands=moderation_commands)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)