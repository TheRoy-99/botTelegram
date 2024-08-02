import sqlite3
import random
import datetime
import schedule
import time
from telebot import TeleBot, types

# Leer el token desde un archivo
with open('Token.txt', 'r') as file:
    token = file.read().strip()

# Inicializa el bot con el token leído
bot = TeleBot(token)

# Conexión a la base de datos SQLite
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        interests TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reminders (
        user_id INTEGER,
        text TEXT,
        reminder_datetime TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS packages (
        user_id INTEGER,
        tracking_number TEXT,
        status TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Funcionalidad para establecer recordatorios
@bot.message_handler(commands=["reminder"])
def set_reminder(message):
    bot.send_message(message.chat.id, "Envía el recordatorio en el formato: 'Recordatorio; Fecha (YYYY-MM-DD); Hora (HH:MM)'")
    bot.register_next_step_handler(message, handle_reminder)

def handle_reminder(message):
    try:
        parts = message.text.split(';')
        if len(parts) != 3:
            raise ValueError("Número de partes incorrecto")
        
        reminder_text = parts[0].strip()
        date_str = parts[1].strip()
        time_str = parts[2].strip()

        # Verifica el formato de la fecha y hora
        reminder_datetime_str = f"{date_str} {time_str}"
        reminder_datetime = datetime.datetime.strptime(reminder_datetime_str, "%Y-%m-%d %H:%M").isoformat()
        
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO reminders (user_id, text, reminder_datetime) VALUES (?, ?, ?)',
                       (message.chat.id, reminder_text, reminder_datetime))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"Recordatorio establecido para {reminder_datetime}")
    except ValueError as e:
        bot.reply_to(message, f"Error en el formato. {e}. Usa el formato correcto: 'Recordatorio; Fecha (YYYY-MM-DD); Hora (HH:MM)'")
    except Exception as e:
        bot.reply_to(message, f"Error inesperado: {e}")

# Funcionalidad para noticias y actualizaciones
@bot.message_handler(commands=["subscribe"])
def subscribe(message):
    bot.send_message(message.chat.id, "¿Sobre qué tema te gustaría recibir noticias o actualizaciones?")
    bot.register_next_step_handler(message, handle_subscription)

def handle_subscription(message):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO users (user_id, username, interests) VALUES (?, ?, ?)',
                   (message.chat.id, message.from_user.username, message.text))
    conn.commit()
    conn.close()
    bot.reply_to(message, f"Te has suscrito a noticias sobre: {message.text}")

def send_updates():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, interests FROM users')
    users = cursor.fetchall()
    for user_id, interest in users:
        bot.send_message(user_id, f"Aquí tienes las últimas noticias sobre {interest}.")
    conn.close()

# Funcionalidad para recetas
@bot.message_handler(commands=["recipe"])
def get_recipe(message):
    recipes = [
        "Ensalada de pollo: Cocina pechugas de pollo, mezcla con verduras frescas y adereza al gusto.",
        "Sopa de tomate: Cocina tomates, cebolla y ajo, licúa y sazona.",
        "Pasta con pesto: Cocina pasta y mezcla con pesto casero.",
    ]
    recipe = random.choice(recipes)
    bot.reply_to(message, f"Receta recomendada: {recipe}")

# Funcionalidad para trivia
@bot.message_handler(commands=["trivia"])
def trivia(message):
    trivia_questions = [
        {"question": "¿Cuál es la capital de Francia?", "answer": "París"},
        {"question": "¿En qué año llegó el hombre a la Luna?", "answer": "1969"},
        {"question": "¿Quién escribió 'Cien años de soledad'?", "answer": "Gabriel García Márquez"},
    ]
    question = random.choice(trivia_questions)
    bot.send_message(message.chat.id, question["question"])
    bot.register_next_step_handler(message, lambda msg: check_trivia_answer(msg, question["answer"]))

def check_trivia_answer(message, correct_answer):
    if message.text.lower() == correct_answer.lower():
        bot.reply_to(message, "¡Correcto!")
    else:
        bot.reply_to(message, f"Incorrecto. La respuesta correcta es: {correct_answer}")

# Funcionalidad para seguimiento de paquetes
@bot.message_handler(commands=["track"])
def track_package(message):
    bot.send_message(message.chat.id, "Envía el número de seguimiento del paquete")
    bot.register_next_step_handler(message, handle_tracking)

def handle_tracking(message):
    # Simulación de seguimiento
    tracking_number = message.text
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO packages (user_id, tracking_number, status) VALUES (?, ?, ?)',
                   (message.chat.id, tracking_number, "En tránsito"))
    conn.commit()
    conn.close()
    bot.reply_to(message, f"Estado del paquete con número {tracking_number}: En tránsito")

# Funcionalidad para saludar y manejar mensajes
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    username = message.from_user.username
    bot.reply_to(
        message,
        f"""
        Hola @{username}, soy tu bot. Estos son los comandos disponibles:
        \n /reminder - establecer recordatorios
        \n /recipe - recibir recetas de comidas sencillas
        \n /trivia - jugar trivia de cultura general
        \n /track - seguir paquetes o envíos
        \n /subscribe - suscribirse a noticias o actualizaciones
        """
    )

@bot.message_handler(content_types=["text"])
def handle_text(message):
    username = message.from_user.username
    if message.text.lower() in ["hola", "hello", "hi"]:
        bot.send_message(
            message.chat.id,
            f"Hola @{username}, ¿en qué te puedo ayudar?",
        )
    else:
        bot.send_message(
            message.chat.id,
            "Comando no encontrado. Por favor, usa /start para revisar los comandos disponibles",
        )

# Función para verificar y enviar recordatorios
def check_reminders():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    while True:
        now = datetime.datetime.now().isoformat()
        cursor.execute('SELECT user_id, text FROM reminders WHERE reminder_datetime <= ?', (now,))
        reminders = cursor.fetchall()
        for user_id, reminder_text in reminders:
            bot.send_message(user_id, f"Recordatorio: {reminder_text}")
            cursor.execute('DELETE FROM reminders WHERE user_id = ? AND text = ?', (user_id, reminder_text))
        conn.commit()
        time.sleep(60)  # Verificar cada minuto

# Programar tareas
schedule.every().day.at("09:00").do(send_updates)  # Enviar actualizaciones diarias a las 09:00

# Iniciar el bot y el chequeo de recordatorios
import threading
threading.Thread(target=check_reminders).start()

while True:
    schedule.run_pending()
    bot.polling(none_stop=True)
    time.sleep(1)
