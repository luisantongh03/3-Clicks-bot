import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai
from PIL import Image

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Obtener tokens de las variables de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Faltan TELEGRAM_TOKEN o GEMINI_API_KEY en las variables de entorno.")

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Avisar que estamos analizando
    msg = await update.message.reply_text("🔍 Analizando gráfico de trading... Por favor espera un momento.")
    
    try:
        # Descargar la foto enviada por el usuario
        photo_file = await update.message.photo[-1].get_file()
        photo_path = "temp_chart.jpg"
        await photo_file.download_to_drive(photo_path)
        
        # Abrir la imagen con PIL
        img = Image.open(photo_path)
        
        # Prompt enfocado en trading de 3 clics
        prompt = (
            "Eres un experto trader profesional en opciones binarias y análisis técnico. "
            "Analiza esta captura de pantalla de un gráfico de trading. "
            "Proporciona un análisis técnico rápido y claro basado en la estrategia de 3 clics: "
            "1. Tendencia principal actual. "
            "2. Niveles clave de soporte/resistencia visibles o acción del precio reciente. "
            "3. Señal clara de operación (COMPRA/CALL o VENTA/PUT) con un nivel de confianza (Alto/Medio/Bajo) y una justificación breve y directa."
        )
        
        # Enviar a Gemini
        response = model.generate_content([prompt, img])
        
        # Enviar el resultado al usuario
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text=response.text
        )
        
        # Limpiar archivo temporal
        if os.path.exists(photo_path):
            os.remove(photo_path)
            
    except Exception as e:
        logging.error(f"Error procesando la imagen: {e}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text="❌ Ocurrió un error al procesar el gráfico. Asegúrate de que la imagen sea clara y vuelve a intentarlo."
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola, trader! 🚀 Envíame una captura de pantalla de tu gráfico y te daré el análisis técnico inmediato para operar."
    )

def main():
    # Construir la aplicación usando la forma moderna y recomendada
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Manejadores
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.COMMAND, start))
    
    print("Bot iniciado correctamente y escuchando...")
    app.run_polling()

if __name__ == '__main__':
    main()
