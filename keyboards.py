from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_kb(menu: dict) -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text=menu["button_order_exchange"]),
            KeyboardButton(text=menu["button_course"])
        ],
        [
            KeyboardButton(text=menu["button_reviews"]),
            KeyboardButton(text=menu["button_guide"])
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard

def get_dialog_kb(menu: dict) -> ReplyKeyboardMarkup:
    close_kb = [
        [
            KeyboardButton(text=menu["button_return_to_bot"]),
            KeyboardButton(text=menu["button_give_review"])
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=close_kb,
        resize_keyboard=True
    )
    return keyboard