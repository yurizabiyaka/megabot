import telebot
import mysql.connector
import os
from datetime import datetime
import openai

# Initialize the Telegram bot
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'dbuser',
    'password': 'dbpass',
    'database': 'db'
}

class Database:
    def __init__(self):
        self.connection = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                model_name VARCHAR(50) DEFAULT 'chatgpt-4o-latest',
                registration_date DATETIME,
                last_active DATETIME
            )
        ''')
        self.connection.commit()

    def register_user(self, user_id, username):
        try:
            self.cursor.execute('''
                INSERT INTO users (user_id, username, registration_date, last_active)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE last_active = %s
            ''', (user_id, username, datetime.now(), datetime.now(), datetime.now()))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error registering user: {e}")
            return False

    def get_user_model(self, user_id):
        self.cursor.execute('SELECT model_name FROM users WHERE user_id = %s', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 'chatgpt-4o-latest'

    def get_default_model(self):
        return 'chatgpt-4o-latest'

class LLMHandler:
    def __init__(self):
        # Initialize the OpenAI client with the API key
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def process_request(self, model_name, prompt):
        try:
            if model_name.startswith('gpt') or model_name.startswith('chatgpt'):
                # Use the new client to create a chat completion
                completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=model_name
                )
                # Extract and return the response content
                return completion.choices[0].message.content
            else:
                return "Unsupported model"
        except Exception as e:
            return f"Error processing request: {e}"


# Initialize database
db = Database()
llm_handler = LLMHandler()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username

    if db.register_user(user_id, username):
        welcome_message = (
            f"Welcome to the LLM Bot!\n"
            f"You're registered with {db.get_default_model()} as your default model.\n"
            f"Just send me your question, and I'll process it."
        )
    else:
        welcome_message = "Welcome back! Just send me your question."

    bot.reply_to(message, welcome_message)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_input = message.text

    # Get user's selected model
    model_name = db.get_user_model(user_id)

    # Process the request through LLM
    response = llm_handler.process_request(model_name, user_input)

    # Format and send response
    if len(response) > 4096:
        # Split long messages due to Telegram's message length limit
        for i in range(0, len(response), 4096):
            bot.reply_to(message, response[i:i + 4096])
    else:
        bot.reply_to(message, response)

if __name__ == "__main__":
    print("Bot is running...")
    bot.polling(none_stop=True)

