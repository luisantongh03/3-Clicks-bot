import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from PIL import Image
import io

# Configuración de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Cargar variables de entorno
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

PROMPT_ANALISIS = """
Eres un analista experto en trading técnico de velas japonesas y acción del precio.
Analiza detenidamente la imagen del gráfico que te acaban de enviar y proporciona un análisis estructurado y directo:

1. **Tendencia Principal**: (Alcista, Bajista o Lateral / Consolidada).
2. **Niveles Clave**: Soporte y Resistencia inmediatos que identifiques.
3. **Patrones de Velas**: Estructura o patrón visual relevante en las últimas velas.
4. **Sugerencia Operativa**: (Entrada a la COMPRA / CALL, VENTA / PUT, o ESPERAR / SIN SEÑAL CLARA). Justifica tu recomendación de forma breve y precisa.

Mantén un lenguaje claro, profesional y directo.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu asistente visual de trading.\n\n"
        "Envíame una captura de pantalla de cualquier gráfico de velas (Quotex, Pocket Option, etc.) y la analizaré con visión de inteligencia artificial."
    )

async def analizar_imagen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🔍 Analizando gráfico... Por favor espera unos segundos.")
    
    try:
        # Descargar la foto enviada
        foto = await update.message.photo[-1].get_file()
        foto_bytes = await foto.download_as_bytearray()
        
        # Convertir a imagen PIL
        imagen = Image.open(io.BytesIO(foto_bytes))
        
        # Enviar a Gemini Vision
        response = model.generate_content([PROMPT_ANALISIS, imagen])
        
        # Responder al usuario
        await msg.edit_text(response.text, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Error al procesar la imagen: {e}")
        await msg.edit_text("❌ Ocurrió un error al analizar la imagen. Intenta enviarla nuevamente o verifica que sea un gráfico claro.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analizar_imagen))
    
    print("Bot en marcha...")
    app.run_polling()
    
