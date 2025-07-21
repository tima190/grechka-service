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
    if callback.data == "order_art":
        # Для арта
        builder = InlineKeyboardBuilder()
        builder.add(
            types.InlineKeyboardButton(
                text="📝 Заполнить анкету", callback_data="fill_art_form"
            )
        )
        await callback.message.edit_text(
            "🎨 Условия заказа арт‑работы:\n"
            "• Срок: 3–7 дней\n"
            "• Предоплата: 50%\n"
            "• Правка: по скетчу\n\n"
            "💰 Примерные цены:\n"
            "• Портрет: 1500 ₽\n"
            "• До пояса: 2000 ₽\n"
            "• Полный рост: 2500–3500 ₽\n"
            "• Скетч: от 300 ₽, Лайн: от 700 ₽\n"
            "• Дополнительно: второй персонаж +50%, фон +300–1000 ₽",
            reply_markup=builder.as_markup(),
        )

        await state.set_state(OrderStates.ART_ORDER)

    if callback.data == "order_program":
        # Для программы
        builder = InlineKeyboardBuilder()
        builder.add(
            types.InlineKeyboardButton(
                text="📝 Заполнить анкету", callback_data="fill_program_form"
            )
        )
        await callback.message.edit_text(
            "💻 Условия заказа разработки:\n"
            "• Срок: от 2 недель\n"
            "• Требуется ТЗ\n"
            "• Предоплата: по договорённости",
            reply_markup=builder.as_markup(),
        )
        await state.set_state(OrderStates.PROGRAM_ORDER)


# ===== Обработка анкет =====


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


# Прием анкеты для арта
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


# Инициализация заполнения анкеты для программы (пошаговый вариант)
@dp.callback_query(OrderStates.PROGRAM_ORDER, F.data == "fill_program_form")
async def start_program_form(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.FILLING_PROGRAM_FORM)
    await state.update_data(steps=[])  # Хранение ответов
    await callback.message.answer(
        "📝 Анкета (1/5): Опишите цель программы\n"
        "Например: «Онлайн‑учёт задач для небольшой команды»"
    )


# Пошаговая обработка анкеты для программы
@dp.message(OrderStates.FILLING_PROGRAM_FORM)
async def process_program_form_step(message: types.Message, state: FSMContext):
    data = await state.get_data()
    steps = data.get("steps", [])
    steps.append(message.text)

    if len(steps) == 1:
        await message.answer(
            "📝 Анкета (2/5): Какие функции нужны?\n"
            "Примеры: регистрация, отчёты, экспорт в PDF"
        )
        await state.update_data(steps=steps)
    elif len(steps) == 2:
        await message.answer(
            "📝 Анкета (3/5): Технические требования\n"
            "Примеры: веб‑приложение на React, интеграция с CRM"
        )
        await state.update_data(steps=steps)
    elif len(steps) == 3:
        await message.answer(
            "📝 Анкета (4/5): Сроки и бюджет\nПример: 1–2 месяца, бюджет 10,000-30,000 RUB"
        )
        await state.update_data(steps=steps)
    elif len(steps) == 4:
        await message.answer(
            "📝 Анкета (5/5): Ваши контакты для связи\n"
            "Телефон, email, Telegram и удобное время для созвона"
        )
        await state.update_data(steps=steps)
    else:
        # Финализация анкеты
        form_text = "\n\n".join(
            [
                f"1. Назначение: {steps[0]}",
                f"2. Функционал: {steps[1]}",
                f"3. Требования: {steps[2]}",
                f"4. Бюджет/Сроки: {steps[3]}",
                f"5. контакты: {steps[3]}",
            ]
        )

        # Отправка в спецчат
        await bot.send_message(
            chat_id=SPECIAL_CHAT_ID,
            text=f"🚀 Новая заявка на программу!\n\n"
            f"От: @{message.from_user.username}\n"
            f"Данные:\n{form_text}",
        )
        await message.answer(
            "✅ Ваша заявка принята!\nЖдите ответа по контактам, либо в личных сообщениях"
        )
        await state.clear()


# ===== Запуск =====
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
