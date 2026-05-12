"""
Telegram bot handler.
Manages commands and free-text queries for the Roger chatbot.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode, ChatAction
from app.knowledge_service import (
    get_all_tablas,
    get_tabla_by_name,
    get_diccionario_by_tabla,
    get_all_flujos,
    get_flujo_by_name,
    search_all,
)
from app.ai_service import generate_response
from app.config import GCS_BUCKET_NAME

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Command Handlers
# ──────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome = (
        "🏛️ *¡Bienvenido a Roger!*\n\n"
        "Soy tu asistente de *Arquitectura Empresarial* y "
        "*Gobierno del Dato* del IDEAM.\n\n"
        "Puedo ayudarte con:\n"
        "📊 Consultas sobre *datos maestros* y tablas OSPA\n"
        "📋 *Diccionario de datos* institucional\n"
        "🔄 *Flujos de información* (ArchiMate)\n"
        "🔍 *Búsquedas* en toda la base de conocimiento\n\n"
        "Usa /help para ver los comandos disponibles o "
        "simplemente escríbeme tu pregunta en lenguaje natural."
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "📖 *Comandos Disponibles*\n\n"
        "🏠 /start — Inicio y bienvenida\n"
        "❓ /help — Esta ayuda\n"
        "📊 /tablas — Lista de datos maestros\n"
        "📋 /diccionario `<tabla>` — Variables de una tabla\n"
        "🔄 /flujos — Flujos de información\n"
        "🔍 /buscar `<término>` — Búsqueda global\n\n"
        "💬 *Texto libre*: Escribe cualquier pregunta sobre "
        "arquitectura empresarial o gobierno del dato del IDEAM "
        "y te responderé con IA.\n\n"
        "_Ejemplos:_\n"
        '• "¿Qué variables tiene la tabla ALERTAS\\_IDD?"\n'
        '• "¿Cómo fluyen los datos de precipitación?"\n'
        '• "¿Cuáles tablas tienen datos georreferenciados?"'
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def cmd_tablas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tablas command - list all master data tables."""
    await update.message.chat.send_action(action=ChatAction.TYPING)

    tablas = get_all_tablas()
    if not tablas:
        await update.message.reply_text(
            "⚠️ No se encontraron tablas en la base de conocimiento."
        )
        return

    text = "📊 *Datos Maestros — OSPA/IDEAM*\n\n"
    for i, t in enumerate(tablas, 1):
        nombre = t.get("nombre_tabla", "N/A")
        desc = t.get("descripcion", "")[:100]
        attrs = ", ".join(t.get("atributos", []))
        geo = "🌍" if t.get("georreferenciado") == "Sí" else ""
        text += (
            f"*{i}. {nombre}* {geo}\n"
            f"   _{desc}_\n"
            f"   📌 Atributos: `{attrs}`\n\n"
        )

    text += f"_Total: {len(tablas)} tablas | Usa /diccionario <nombre> para detalles_"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_diccionario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /diccionario <tabla> command."""
    await update.message.chat.send_action(action=ChatAction.TYPING)

    if not context.args:
        await update.message.reply_text(
            "📋 Uso: /diccionario `<nombre_tabla>`\n\n"
            "Ejemplo: /diccionario precipitacion\n\n"
            "Usa /tablas para ver las tablas disponibles.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    query = " ".join(context.args)
    variables = get_diccionario_by_tabla(query)

    if not variables:
        await update.message.reply_text(
            f"⚠️ No se encontraron variables para '{query}'.\n"
            "Usa /tablas para ver los nombres correctos.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Group by file
    archivo = variables[0].get("nombre_archivo", query)
    desc_archivo = variables[0].get("descripcion_archivo", "")

    text = f"📋 *Diccionario: {archivo}*\n"
    if desc_archivo:
        text += f"_{desc_archivo[:120]}_\n\n"
    else:
        text += "\n"

    for v in variables[:15]:  # Limit to avoid message length issues
        nombre = v.get("nombre_variable", "N/A")
        tipo = v.get("tipo_dato", "N/A")
        desc = v.get("descripcion_variable", "")[:80]
        pk = " 🔑" if v.get("llave_primaria") else ""
        fk = " 🔗" if v.get("llave_foranea") else ""

        text += f"• *{nombre}*{pk}{fk} (`{tipo}`)\n  _{desc}_\n\n"

    if len(variables) > 15:
        text += f"_...y {len(variables) - 15} variables más._\n"

    text += "\n🔑 = Llave Primaria | 🔗 = Llave Foránea"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_flujos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /flujos command - list all information flows."""
    await update.message.chat.send_action(action=ChatAction.TYPING)

    flujos = get_all_flujos()
    if not flujos:
        await update.message.reply_text(
            "⚠️ No se encontraron flujos en la base de conocimiento."
        )
        return

    text = "🔄 *Flujos de Información — IDEAM*\n\n"
    keyboard = []

    for i, f in enumerate(flujos, 1):
        nombre = f.get("nombre", "N/A")
        desc = f.get("descripcion", "")[:100]
        etapas = " → ".join(f.get("etapas", []))

        text += (
            f"*{i}. {nombre}*\n"
            f"   _{desc}_\n"
            f"   🔄 {etapas}\n\n"
        )

        # Add inline keyboard button for image
        if f.get("imagen"):
            keyboard.append([
                InlineKeyboardButton(
                    f"📷 Ver diagrama: {nombre[:30]}",
                    callback_data=f"flujo_{f['id']}",
                )
            ])

    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def callback_flujo_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback for flow diagram image request."""
    query = update.callback_query
    await query.answer()

    flujo_id = query.data.replace("flujo_", "")
    flujos = get_all_flujos()
    flujo = next((f for f in flujos if f.get("id") == flujo_id), None)

    if flujo and flujo.get("imagen_url"):
        try:
            from google.cloud import storage
            client = storage.Client(project="roger-496113")
            bucket = client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(flujo["imagen"])

            # Download to memory and send
            image_data = blob.download_as_bytes()
            from io import BytesIO
            photo = BytesIO(image_data)
            photo.name = f"{flujo_id}.png"

            await query.message.reply_photo(
                photo=photo,
                caption=f"🔄 *{flujo.get('nombre', '')}*\n\n"
                        f"_{flujo.get('descripcion', '')[:200]}_",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            logger.error(f"Error sending flow image: {e}")
            await query.message.reply_text(
                f"⚠️ No pude cargar la imagen del flujo. "
                f"Descripción:\n\n{flujo.get('descripcion', 'N/A')}"
            )
    else:
        await query.message.reply_text("⚠️ No se encontró la imagen del flujo.")


async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buscar <term> command - global search."""
    await update.message.chat.send_action(action=ChatAction.TYPING)

    if not context.args:
        await update.message.reply_text(
            "🔍 Uso: /buscar `<término>`\n\n"
            "Ejemplo: /buscar precipitacion\n"
            "Ejemplo: /buscar CODIGO",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    query = " ".join(context.args)
    results = search_all(query)

    total = sum(len(v) for v in results.values())
    if total == 0:
        await update.message.reply_text(
            f"🔍 No se encontraron resultados para '{query}'.\n"
            "Intenta con otro término.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    text = f"🔍 *Resultados para '{query}'*\n\n"

    if results["tablas"]:
        text += f"📊 *Tablas ({len(results['tablas'])}):*\n"
        for t in results["tablas"][:5]:
            text += f"  • {t.get('nombre_tabla', 'N/A')}\n"
        text += "\n"

    if results["variables"]:
        text += f"📋 *Variables ({len(results['variables'])}):*\n"
        for v in results["variables"][:8]:
            text += (
                f"  • `{v.get('nombre_variable', 'N/A')}` "
                f"({v.get('tipo_dato', '')}) — {v.get('nombre_archivo', '')}\n"
            )
        text += "\n"

    if results["flujos"]:
        text += f"🔄 *Flujos ({len(results['flujos'])}):*\n"
        for f in results["flujos"][:5]:
            text += f"  • {f.get('nombre', 'N/A')}\n"

    text += f"\n_Total: {total} resultados_"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle free-text messages with AI-powered responses."""
    await update.message.chat.send_action(action=ChatAction.TYPING)

    user_message = update.message.text
    logger.info(f"User message: {user_message[:100]}")

    # Generate AI response with RAG
    response = generate_response(user_message)

    # Telegram has a 4096 char limit for messages
    if len(response) > 4000:
        # Split into chunks
        chunks = [response[i:i + 4000] for i in range(0, len(response), 4000)]
        for chunk in chunks:
            try:
                await update.message.reply_text(
                    chunk, parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                # Fallback without markdown if parsing fails
                await update.message.reply_text(chunk)
    else:
        try:
            await update.message.reply_text(
                response, parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            # Fallback without markdown if parsing fails
            await update.message.reply_text(response)


def register_handlers(app: Application):
    """Register all handlers with the Telegram application."""
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("tablas", cmd_tablas))
    app.add_handler(CommandHandler("diccionario", cmd_diccionario))
    app.add_handler(CommandHandler("flujos", cmd_flujos))
    app.add_handler(CommandHandler("buscar", cmd_buscar))
    app.add_handler(CallbackQueryHandler(callback_flujo_image, pattern=r"^flujo_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
