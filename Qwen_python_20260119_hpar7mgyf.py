import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from openai import AsyncOpenAI
from rag_engine import retrieve_context, load_knowledge
from calculations import calculate_ytm, calculate_sharpe, calculate_pe

load_dotenv()
logging.basicConfig(level=logging.INFO)

# Загрузка базы знаний
load_knowledge()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    questions = [
        "Что показывает коэффициент бета?",
        "Как рассчитать доходность к погашению (YTM) облигации?",
        "Что такое эффективный портфель по Марковицу?"
    ]
    context.user_data['test_question'] = questions[0]
    await update.message.reply_text(f"📝 Вопрос:\n{questions[0]}\n\nНапишите ваш ответ:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # Режим теста
    if 'test_question' in context.user_data:
        question = context.user_data['test_question']
        prompt = f"""
Оцени ответ студента по шкале от 0 до 100. Используй только цифру.

Правильный ответ должен включать:
- Для бета: меру систематического риска относительно рынка.
- Максимум 100 баллов за полноту, точность и ясность.

Вопрос: {question}
Ответ студента: {text}

Оценка (только число):
"""
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        score = response.choices[0].message.content.strip()
        await update.message.reply_text(f"Ваша оценка: **{score}/100**\nХотите новый вопрос? Напишите /test", parse_mode="Markdown")
        context.user_data.pop('test_question', None)
        return

    # Автоматическое распознавание задач
    if "ytm" in text.lower() or "доходность к погашению" in text.lower():
        # Пример: "облигация 1000, купон 8%, 3 года, цена 950"
        # Здесь можно добавить парсер — пока просто объяснение
        explanation = (
            "Для расчёта YTM нужны: номинал, купон, срок, цена.\n"
            "Пример: номинал=1000, купон=80, срок=3, цена=950 → YTM ≈ 9.87%.\n"
            "Хочешь, чтобы я посчитал по твоим данным? Напиши: YTM номинал=... купон=... срок=... цена=..."
        )
        await update.message.reply_text(explanation)
        return

    # Обычный запрос → RAG + LLM
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
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        answer = response.choices[0].message.content
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