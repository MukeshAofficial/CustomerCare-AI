import telebot
import google.generativeai as genai
from flask import Flask, request, jsonify
import base64
import io
from PIL import Image

# Replace with your Telegram bot token and Gemini API key
TELEGRAM_BOT_TOKEN = ''
GEMINI_API_KEY = ''

# Initialize the bot and the Gemini API
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# Create a Flask app to handle webhooks
app = Flask(__name__)

# Function to process images and get the description from Gemini LLM
def process_image(image_data):
    # Load the image
    img = Image.open(io.BytesIO(image_data))

    # Use Generative AI model to generate a description of the image
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = "You are an customer support agent of amazon act like a human and answer to user queries in one or 3 lines based on the image "
    response = model.generate_content([prompt, img], stream=False)
    
    return response.text  # Extracted text description

# Route to handle LLM response generation for text input
@app.route('/get_response', methods=['POST'])
def get_response():
    data = request.json
    user_message = data.get('message', '')

    # Use the Google Gemini LLM to generate a response
    model = genai.GenerativeModel('gemini-1.5-flash')
    rply = model.generate_content(f"{user_message} You are an customer support agent of amazon act like a human and answer to user queries in one or two lines without any */ symbols")
    
    return jsonify({'response': rply.text})

# Handle the /start command on Telegram
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hi! I'm a  AI Powered Customer Bot. Send me an image or ask me anything!")

# Handle regular text messages from users
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_message(message):
    user_message = message.text
    
    # Call the Flask API to generate a response from the LLM
    with app.test_client() as client:
        response = client.post('/get_response', json={'message': user_message})
        bot_reply = response.get_json().get('response', 'No response received.')

    # Reply to the user with the LLM response
    bot.reply_to(message, bot_reply)

# Handle images sent by the user
@bot.message_handler(content_types=['photo'])
def handle_image(message):
    # Get the image file from the message
    file_info = bot.get_file(message.photo[-1].file_id)
    file_data = bot.download_file(file_info.file_path)
    
    # Process the image using Gemini LLM
    description = process_image(file_data)

    # Send the description back to the user
    bot.reply_to(message, description)

# Polling to keep the bot running and listening for updates
if __name__ == "__main__":
    bot.polling()
