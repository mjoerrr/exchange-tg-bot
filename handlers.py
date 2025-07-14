import asyncio
import aiohttp
from datetime import datetime
from aiogram import Bot, Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.command import Command

from config import MODERS_CHAT_ID
from database import (
    cmd_start_db, add_message_to_db, clear_message_db, get_message_history,
    made_new_topic_db_adder, add_id_to_topic, checker_to_add_new_topic, cur, db, cur_topic
)
from keyboards import get_main_kb, get_dialog_kb
from utils import get_menu_text, ZaprosStage, numb_maker, money_format

menu = get_menu_text()
main_kb = get_main_kb(menu)
dialog_kb = get_dialog_kb(menu)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    await message.answer(menu["info_hello"], reply_markup=main_kb)
    await cmd_start_db(message.chat.id)
    await state.set_state(ZaprosStage.NO_ZAPROS)


# При нажатии на кнопку "заказать обмен"
@router.message(F.text == menu["button_order_exchange"])
async def send_get_exchange(message: types.Message, state: FSMContext, bot: Bot):
    if await checker_to_add_new_topic(message.chat.id):
        start_time_info = cur.execute("SELECT start_message_date FROM users WHERE id == ?", (message.chat.id,)).fetchone()
        start_time = start_time_info[0] if start_time_info else "Неизвестно"

        await message.answer(
            menu["info_open_chat_with_manager"],
            reply_markup=dialog_kb
        )
        await asyncio.sleep(1.5)
        await message.answer(menu["manager_answer"])

        new_chat = await bot.create_forum_topic(MODERS_CHAT_ID, f'Чат с клиентом id {message.chat.id}')
        topic_id = new_chat.message_thread_id

        made_new_topic_db_adder(message.chat.id, topic_id)
        add_id_to_topic(message.chat.id, topic_id)
        cur.execute("UPDATE users SET last_message_date = ? WHERE id == ?",
                    (datetime.now().strftime("%d.%m.%Y %H:%M:%S"), message.chat.id))
        db.commit()

        message_history = await get_message_history(message.chat.id)
        message_history_str = '\n\n'.join(message_history)
        await bot.send_message(
            chat_id=MODERS_CHAT_ID,
            message_thread_id=topic_id,
            text=f'<blockquote>{message_history_str}</blockquote>\nКлиент создал чат\n\nЗапустил бота: {start_time}\nID: {message.chat.id}\nПользователь: {message.from_user.first_name}\nНикнейм: @{message.from_user.username}'
        )
    else:
        await message.answer(menu["info_chat_not_closed"], reply_markup=dialog_kb)
        # Обновляем время последнего сообщения, чтобы продлить "активность" топика
        cur.execute("UPDATE users SET last_message_date = ? WHERE id == ?",
                    (datetime.now().strftime("%d.%m.%Y %H:%M:%S"), message.chat.id))
        db.commit()
    await state.set_state(ZaprosStage.CONTINUE_ZAPROS)


# При нажатии на кнопку "текущий курс"
@router.message(F.text == menu["button_course"])
async def send_course(message: types.Message, state: FSMContext):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"http://market.demo-domain.ru/post.php?amount=",
                                    data={'key': 'value'}, headers={'Pragma': 'no-cache'}) as r:
                r.raise_for_status()
                osn_course_str = await r.text()
                osn_course = float(osn_course_str)

        course_text_template = menu["info_showcources"]
        formatted_course_text = course_text_template.format(
            str(osn_course + menu["price < 20000"]),
            str(osn_course + menu["price 20000 - 50000"]),
            str(osn_course + menu["price 50000 - 100000"]),
            str(osn_course + menu["price >100000"])
        )
        await message.answer(formatted_course_text)
    except aiohttp.ClientError as e:
        await message.answer("Произошла ошибка при получении курса. Пожалуйста, попробуйте позже.")
        print(f"Ошибка при запросе курса: {e}")
    except ValueError:
        await message.answer("Не удалось обработать ответ от сервера курса. Пожалуйста, попробуйте позже.")
        print(f"Ошибка при парсинге курса: {osn_course_str}")


# При нажатии на кнопку "отзывы"
@router.message(F.text == menu["button_reviews"])
async def send_reviews(message: types.Message, state: FSMContext):
    await message.answer(menu["info_review_from_main_keybord"])


# При нажатии на кнопку "как происходит обмен"
@router.message(F.text == menu["button_guide"])
async def send_info_guide(message: types.Message, state: FSMContext):
    await message.answer(menu["info_guide"])


# При нажатии на кнопку "вернуться в бота"
@router.message(F.text == menu["button_return_to_bot"])
async def get_back_to_bot(message: types.Message, state: FSMContext):
    await message.answer(menu["info_return_to_bot"], reply_markup=main_kb)
    await clear_message_db(message.chat.id)
    await state.set_state(ZaprosStage.NO_ZAPROS)


# При нажатии на кнопку "оставить отзыв"
@router.message(F.text == menu["button_give_review"])
async def get_review_to_bot(message: types.Message, state: FSMContext):
    await message.answer(menu["info_text_to_get_review"], reply_markup=dialog_kb)
    await state.set_state(ZaprosStage.CONTINUE_ZAPROS)


# При вводе каких-то значений в бота (кроме команд и кнопок)
@router.message(F.chat.type != 'supergroup', F.from_user.is_bot == False)
async def handle_user_input(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state != ZaprosStage.CONTINUE_ZAPROS:
        await add_message_to_db(message.chat.id, message.text)
        try:
            amount_str = numb_maker(message.text)
            if not amount_str: # Если не удалось извлечь число
                await message.answer(menu["info_hello"], reply_markup=main_kb)
                return

            amount = int(amount_str)

            async with aiohttp.ClientSession() as session:
                async with session.post(url=f"http://market.demo-domain.ru/post.php?amount={str(amount)}",
                                        data={'key': 'value'}, headers={'Pragma': 'no-cache'}) as r:
                    r.raise_for_status()
                    course_str = await r.text()
            course = float(course_str)

            if 'бат' in message.text.lower():
                response_text = f'Вы можете обменять {money_format(amount)} бат на {money_format(amount * course)} российских рублей c курсом {course} рублей за 1 тайский бат\n\nДля открытия сделки, нажмите на кнопку "Заказать обмен"'
            else:
                response_text = f'Вы можете обменять {money_format(amount)} рублей на {money_format(amount / course)} тайских бат c курсом {course} рублей за 1 тайский бат\n\nДля открытия сделки, нажмите на кнопку "Заказать обмен"'

            await message.answer(response_text, reply_markup=main_kb)
            await add_message_to_db(message.chat.id, response_text)
        except (ValueError, aiohttp.ClientError) as err:
            print(f"Ошибка при обработке суммы или запросе курса: {err}")
            await message.answer(menu["info_hello"], reply_markup=main_kb)
    else:
        topic_id_info = cur.execute("SELECT topic_id FROM users WHERE id == ?", (message.chat.id,)).fetchone()
        if topic_id_info and topic_id_info[0]:
            thread_id = topic_id_info[0]
            await message.copy_to(chat_id=MODERS_CHAT_ID, message_thread_id=thread_id)
            cur.execute("UPDATE users SET last_message_date = ? WHERE id == ?",
                        (datetime.now().strftime("%d.%m.%Y %H:%M:%S"), message.chat.id))
            db.commit()
            await add_message_to_db(message.chat.id, message.text)
        else:
            await message.answer(menu["info_return_to_bot"], reply_markup=main_kb)
            await clear_message_db(message.chat.id)
            await state.set_state(ZaprosStage.NO_ZAPROS)


# При вводе какого-то текста в группу менеджеров
@router.message(F.chat.type == 'supergroup', F.from_user.is_bot == False)
async def send_message_from_moderator(message: types.Message, bot: Bot):
    if message.message_thread_id:
        user_id_info = cur_topic.execute("SELECT id FROM topics WHERE topic_id == ?", (message.message_thread_id,)).fetchone()
        if user_id_info and user_id_info[0]:
            chat_id = user_id_info[0]
            await message.copy_to(chat_id)
        else:
            await message.answer("Не удалось найти пользователя для этого топика.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Закрыть диалог", callback_data="close")]
            ]))
    else:
        await message.answer("Это сообщение не относится к конкретному топику с пользователем.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Закрыть диалог", callback_data="close")]
        ]))