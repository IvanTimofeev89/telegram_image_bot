import os
from random import choice
from datetime import datetime

from sqlalchemy.sql import select

import telebot
from telebot import types
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from models import ImageBase, session

load_dotenv()

welcome_phrase = os.getenv('WELCOME_PHRASE')
token = os.getenv('TOKEN')

# Инициализация бота
bot = telebot.TeleBot(token)

# Читаем файл с коллекцией фраз и храним их в списке phrase_collection
with open('phrase_collection.txt', 'r', encoding='UTF-8') as file:
    phrase_collection = file.readlines()


class UserImage():

    def __init__(self, message):
        self.id = message.photo[-1].file_id
        self.user_id = message.from_user.id

    def sign_image(self, picture_bytes):
        image = Image.open(BytesIO(picture_bytes))
        image_draw = ImageDraw.Draw(image)

        text = choice(phrase_collection).strip()
        font = ImageFont.truetype("fonts/Lobster-Regular.ttf", size=48, encoding='UTF-8')

        image_width, image_height = image.width, image.height
        text_width = image_draw.textlength(text=text, font=font)

        image_draw.text(((image_width - text_width) / 2, image_height / 2), text=text, font=font, fill='white')

        output_bytes = BytesIO()
        image.save(output_bytes, format='JPEG')
        output_bytes_data = output_bytes.getvalue()

        return output_bytes_data

    def save_image(self, image):
        date_time = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        with open(f"img/{date_time}_{self.user_id}.jpg", "wb") as new_image:
            new_image.write(image)
        return new_image.name


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = types.KeyboardButton("Начать")
    markup.add(start_button)
    bot.send_message(message.chat.id, welcome_phrase, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Начать")
def start_again(message):
    bot.send_message(message.chat.id, "Вы уже начали работу с ботом. Загрузите фото")


@bot.message_handler(content_types=['text'])
def echo(message):
    bot.send_message(message.chat.id, f'Введенный текст: {message.text}')


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_image = UserImage(message)

    image_path = bot.get_file(user_image.id).file_path
    downloaded_picture = bot.download_file(image_path)

    signed_image = user_image.sign_image(picture_bytes=downloaded_picture)
    saved_image_name = user_image.save_image(image=signed_image)

    data = ImageBase(
        image_id=user_image.id,
        image_path=saved_image_name
    )
    session.add(data)
    session.commit()

    db_id_record = data.id

    with open(saved_image_name, 'rb') as photo:
        bot.send_photo(message.chat.id, photo=photo)

    markup = types.InlineKeyboardMarkup(row_width=1)
    button_share = types.InlineKeyboardButton('Поделиться', callback_data=f'share_{db_id_record}')
    markup.add(button_share)

    bot.send_message(message.chat.id, "Поделитесь новым изображением, если оно Вам понравилось!", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('share_'))
def share_image(call):
    db_id_record = int(call.data.split('_')[-1].strip())
    query = select(ImageBase.image_path).where(ImageBase.id == db_id_record)
    image_path = session.scalar(query)

    if image_path:
        with open(image_path, 'rb') as photo:
            bot.send_photo(call.message.chat.id, photo)
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, text="Изображение не найдено")


bot.polling(none_stop=True)