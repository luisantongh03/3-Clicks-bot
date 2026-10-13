import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from google import genai
from PIL import Image

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Faltan TELEGRAM_TOKEN o GEMINI_API_KEY en las variables de entorno.")

client = genai.Client(api_key=GEMINI_API_KEY)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🔍 Analizando gráfico de trading... Por favor espera un momento.")
    photo_path = "temp_chart.jpg"
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(photo_path)
        
        img = Image.open(photo_path)
        
        prompt = (
            "Eres un experto trader profesional en opciones binarias y análisis técnico. "
            "Analiza esta captura de pantalla de un gráfico de trading. "
            "Proporciona un análisis técnico rápido y claro basado en la estrategia de 3 clics: "
            "1. Tendencia principal actual. "
            "2. Niveles clave de soporte/resistencia visibles o acción del precio reciente. "
            "3. Señal clara de operación (COMPRA/CALL o VENTA/PUT) con un nivel de confianza (Alto/Medio/Bajo) y una justificación breve y directa."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img]
        )
        
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text=response.text
        )
            
    except Exception as e:
        logging.error(f"Error procesando la imagen: {e}", exc_info=True)
        error_msg = f"❌ Error al procesar: {str(e)}"
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text=error_msg[:4000]
        )
    finally:
        if os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except Exception:
                pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola, trader! 🚀 Envíame una captura de pantalla de tu gráfico y te daré el análisis técnico inmediato para operar."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Para recibir tu análisis, envíame directamente la captura de pantalla de tu gráfico de trading. 📊"
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    
    print("Bot iniciado correctamente y escuchando...")
    app.run_polling()

if __name__ == '__main__':
    main()
