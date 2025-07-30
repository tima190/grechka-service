import logging
import os
import sys

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()  # take environment variables

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN")
SPECIAL_CHAT_ID = os.getenv("SPECIAL_CHAT_ID")  # ID чата для заявок

print(f"token:{BOT_TOKEN}\nID:{SPECIAL_CHAT_ID}")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# ===== Классы состояний =====
class OrderStates(StatesGroup):
    SELECTING_CATEGORY = State()
    ART_ORDER = State()
    PROGRAM_ORDER = State()
    FILLING_ART_FORM = State()
    FILLING_PROGRAM_FORM = State()


# ===== Обработчики =====


# Стартовая команда
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="🛍️ Заказать", callback_data="start_order")
    )
    await message.answer(
        "👋 Добро пожаловать! Я помогу вам с заказом.", reply_markup=builder.as_markup()
    )


# Начало заказа
@dp.callback_query(F.data == "start_order")
async def start_order(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="🎨 Заказать арт", callback_data="order_art"),
        types.InlineKeyboardButton(
            text="💻 Заказать программу", callback_data="order_program"
        ),
    )
    builder.adjust(1)

    await callback.message.edit_text(
        "Выберите тип услуги:", reply_markup=builder.as_markup()
    )
    await state.set_state(OrderStates.SELECTING_CATEGORY)


# Выбор категории
@dp.callback_query(
    OrderStates.SELECTING_CATEGORY, F.data.in_(["order_art", "order_program"])
)
async def select_category(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()

    if callback.data == "order_art":
        # Для арта
        builder.add(
            types.InlineKeyboardButton(
                text="📝 Заполнить анкету", callback_data="fill_art_form"
            )
        )
        await callback.message.edit_text(
            "🎨 Хочешь заказать арт? Вот как это работает:\n\n"
            "• ⏳ Сроки: обычно от 3 до 14 дней (всё зависит от сложности)\n"
            "• 💰 Предоплата: 50%, остальное — после готовности\n"
            "• ✏️ Правки возможны на этапе скетча\n\n"
            "📌 Примерные цены:\n"
            "• Портрет: 1500 ₽\n"
            "• До пояса: 2000 ₽\n"
            "• В полный рост: 2500–3500 ₽\n"
            "• Скетч: от 300 ₽\n"
            "• Лайн: от 700 ₽\n"
            "• + Второй персонаж: +50%\n"
            "• + Фон: +300–1000 ₽ (в зависимости от сложности)\n\n"
            "Если всё окей — жми на кнопку и заполняй анкету 📝",
            reply_markup=builder.as_markup(),
        )

        await state.set_state(OrderStates.ART_ORDER)

    else:
        # Для программы (одноэтапная анкета)
        builder.add(
            types.InlineKeyboardButton(
                text="📝 Заполнить анкету", callback_data="fill_program_form"
            )
        )
        await callback.message.edit_text(
            "💻 Хочешь заказать программу? Вот несколько деталей:\n\n"
            "• ⏳ Сроки: обычно от 2 недель — зависит от сложности\n"
            "• 📄 Нужно небольшое ТЗ или просто хорошее описание\n"
            "• 💰 Предоплата — по договорённости, всё обсудим\n\n"
            "Если всё понятно, жми на кнопку ниже и заполни анкету 📝",
            reply_markup=builder.as_markup(),
        )
        await state.set_state(OrderStates.PROGRAM_ORDER)

# Инициализация заполнения анкеты для арта
@dp.callback_query(OrderStates.ART_ORDER, F.data == "fill_art_form")
async def start_art_form(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 Пример анкеты для арт‑заказа:\n\n"
        "1. Тип работы (полноценка, до бедер, портрет)\n"
        "2. Персонажи (человек/персонаж с его описанием)\n"
        "3. Пожелания по позам (сидит, стоит, в движении)\n"
        "4. Бюджет (ориентируйтесь на расценки ниже)\n"
        "5. Дедлайн (точная дата или диапазон: 25 июля, или «до конца месяца»)\n"
        "6. Ваши контакты (телефон, email, Telegram)\n\n"
        "💰 Примерные цены:\n"
        "• Портрет: 1500 ₽\n"
        "• До пояса: 2000 ₽\n"
        "• Полный рост: 2500–3500 ₽\n"
        "• Скетч: от 300 ₽, Лайн: от 700 ₽\n"
        "• Дополнительно: второй персонаж +50%, фон +300–1000 ₽\n\n"
        "Отправьте всё одним сообщением."
    )

    await state.set_state(OrderStates.FILLING_ART_FORM)

# Инициализация заполнения анкеты для программы (одно сообщение)
@dp.callback_query(OrderStates.PROGRAM_ORDER, F.data == "fill_program_form")
async def start_program_form(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 Анкета для заказа разработки:\n\n"
        "1. Назначение программы (цель, бизнес‑задача)\n"
        "2. Основной функционал (список фич)\n"
        "3. Технологии/интеграции (если есть предпочтения)\n"
        "4. Сроки и бюджет\n"
        "5. Контакты для связи (телефон, email, Telegram)\n\n"
        "Отправьте всё одним сообщением, пожалуйста."
    )
    await state.set_state(OrderStates.FILLING_PROGRAM_FORM)


@dp.message(OrderStates.FILLING_ART_FORM)
async def process_art_form(message: types.Message, state: FSMContext):
    # Отправка в спецчат
    await bot.send_message(
        chat_id=SPECIAL_CHAT_ID,
        text=f"🚨 Новая заявка на арт!\n\n"
        f"От: @{message.from_user.username}\n"
        f"Данные:\n{message.text}",
    )
    await message.answer("✅ Ваша заявка принята!")
    await state.clear()

# Прием анкеты для программы
@dp.message(OrderStates.FILLING_PROGRAM_FORM)
async def process_program_form(message: types.Message, state: FSMContext):
    # Отправка в спецчат
    await bot.send_message(
        chat_id=SPECIAL_CHAT_ID,
        text=(
            "🚀 Новая заявка на разработку программы!\n\n"
            f"От: @{message.from_user.username}\n\n"
            "Данные:\n"
            f"{message.text}"
        ),
    )
    await message.answer("✅ Ваша заявка принята!")
    await state.clear()


# ===== Запуск =====
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
