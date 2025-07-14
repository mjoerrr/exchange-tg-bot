import json
from aiogram.fsm.state import StatesGroup, State
from typing import Union

class ZaprosStage(StatesGroup):

    CONTINUE_ZAPROS = State() # Состояние, когда пользователь находится в диалоге с менеджером
    NO_ZAPROS = State()      # Состояние, когда пользователь находится в основном меню
    GIVE_REVIEW = State()    # Состояние для оставления отзыва

def get_menu_text() -> dict:
    with open('texts.json', 'r', encoding='utf-8') as fr:
        menu = json.load(fr)
    return menu

def numb_maker(text: str) -> str:
    text = text.strip()
    if 'тысяч' in text:
        text = text.replace('тысяч', '000')
    if 'тыс' in text:
        text = text.replace('тыс', '000')
    start_numb = ''
    for i in range(len(text)):
        if text[i].isdigit():
            start_numb += text[i]
        elif (i > 0 and (text[i - 1].isdigit() or text[i - 1] == ' ')) and (text[i].lower() == 'к'):
            start_numb += '000'
    return start_numb

def money_format(money: Union[int, float]) -> str:
    return '{:,.0f}'.format(money).replace(',', ' ')
