import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import aiosqlite

TOKEN = os.getenv("BOT_TOKEN")
TEACHER_ID = int(os.getenv("TEACHER_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_NAME = "database.db"

POINTS = {
    "мектеп": 5,
    "аудан": 10,
    "облыс": 20,
    "республика": 30
}

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS students (
            telegram_id INTEGER PRIMARY KEY,
            name TEXT,
            points INTEGER DEFAULT 0
        )
        """)
        await db.commit()

@dp.message(Command("start"))
async def start(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO students (telegram_id, name) VALUES (?, ?)",
            (message.from_user.id, message.from_user.full_name)
        )
        await db.commit()

    await message.answer("Adal-Bot 24/7 жүйесіне қош келдіңіз!\n\nЖетістік қосу үшін жазыңыз: мектеп / аудан / облыс / республика")

@dp.message(lambda m: m.text and m.text.lower() in POINTS)
async def achievement(message: types.Message):
    level = message.text.lower()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✔ Растау", callback_data=f"approve:{message.from_user.id}:{level}")]
    ])

    await bot.send_message(
        TEACHER_ID,
        f"Жаңа жетістік:\nОқушы: {message.from_user.full_name}\nДеңгей: {level}",
        reply_markup=keyboard
    )

    await message.answer("Жетістік мұғалімге жіберілді ⏳")

@dp.callback_query(lambda c: c.data.startswith("approve"))
async def approve(callback: types.CallbackQuery):
    _, student_id, level = callback.data.split(":")
    student_id = int(student_id)
    points = POINTS[level]

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE students SET points = points + ? WHERE telegram_id=?",
            (points, student_id)
        )
        await db.commit()

    await bot.send_message(student_id, f"Сіздің жетістігіңіз расталды! +{points} ұпай ⭐")
    await callback.answer("Ұпай қосылды!")

@dp.message(Command("top"))
async def top(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT name, points FROM students ORDER BY points DESC LIMIT 5"
        )
        rows = await cursor.fetchall()

    text = "🏆 ТОП 5:\n\n"
    for i, row in enumerate(rows, 1):
        text += f"{i}. {row[0]} - {row[1]} ұпай\n"

    await message.answer(text)

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
