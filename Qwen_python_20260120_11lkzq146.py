import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from groq import Groq
from rag_engine import retrieve_context, load_knowledge

load_dotenv()
logging.basicConfig(level=logging.INFO)

# Инициализация
load_knowledge()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 Привет! Я — ИИ-ассистент по рынку ценных бумаг.\n\n"
        "Спроси меня:\n"
        "• Что такое дюрация?\n"
        "• Как считать YTM?\n"
        "• Объясни CAPM\n\n"
        "Или начни тест: /test\n\n"
        "⚠️ Я не даю инвестиционных рекомендаций!"
    )

async def handle_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = "Что показывает коэффициент бета?"
    context.user_data['test_question'] = question
    await update.message.reply_text(f"📝 Вопрос:\n{question}\n\nНапишите ваш ответ:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if 'test_question' in context.user_data:
        question = context.user_data['test_question']
        prompt = f"""
Оцени ответ студента по шкале от 0 до 100. Используй ТОЛЬКО цифру.

Правильный ответ должен включать:
- Для бета: меру систематического риска относительно рынка.
- Максимум 100 баллов за полноту, точность и ясность.

Вопрос: {question}
Ответ студента: {text}

Оценка (только число):
"""
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-70b-versatile",
            temperature=0
        )
        score = chat_completion.choices[0].message.content.strip()
        await update.message.reply_text(f"Ваша оценка: **{score}/100**\nХотите новый вопрос? Напишите /test", parse_mode="Markdown")
        context.user_data.pop('test_question', None)
        return

    # Основной режим
    context_chunks = retrieve_context(text)
    prompt = f"""
Ты — эксперт по инвестициям и рынку ценных бумаг. Отвечай на русском языке чётко, по делу.
Если в контексте есть ответ — используй его. Если нет — скажи: "Не знаю".

Контекст из учебников:
{context_chunks}

Вопрос:
{text}

Ответ:
"""
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-70b-versatile",
            temperature=0.3,
            max_tokens=500
        )
        answer = chat_completion.choices[0].message.content
        await update.message.reply_text(answer, parse_mode="Markdown")
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("Извини, сейчас не могу ответить. Попробуй позже.")

def main():
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", handle_test))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()