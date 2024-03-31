import os
from datetime import datetime
from io import BytesIO
from random import choice

import telebot
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.sql import select
from telebot import types
from telebot.types import Message

from models import ImageBase, session

# Загружаем необходимые переменные окружения
load_dotenv()
welcome_phrase = os.getenv("WELCOME_PHRASE")
token = os.getenv("TOKEN")
TABLE_NAME = os.getenv("TABLE_NAME")

# Инициализация бота
bot = telebot.TeleBot(token)

# Читаем файл с коллекцией фраз и храним их в списке phrase_collection
with open("phrase_collection.txt", "r", encoding="UTF-8") as file:
    phrase_collection = file.readlines()


class UserImage:
    """
    Класс для загружаемых изображений
    """

    def __init__(self, message: Message):
        """
        Записываем уникальный id изображения и id отправителя
        в атрибуты экземпляра класса
        """
        self.id = message.photo[-1].file_id
        self.user_id = message.from_user.id

    def sign_image(self, picture_bytes: bytes) -> Image.Image:
        """
        Нанесение текста на загруженное изображение с использованием Pillow.
        Метод возвращает подписанный объект Image.
        """
        image = Image.open(BytesIO(picture_bytes))
        image_draw = ImageDraw.Draw(image)

        text = choice(phrase_collection).strip()
        font = ImageFont.truetype("fonts/Lobster-Regular.ttf", size=48, encoding="UTF-8")

        image_width, image_height = image.width, image.height
        text_width = image_draw.textlength(text=text, font=font)

        image_draw.text(
            ((image_width - text_width) / 2, image_height / 2), text=text, font=font, fill="white"
        )

        return image

    def save_image(self, image: Image.Image) -> str:
        """
        Метод сохраняет подписанный объект Image в БД, используя SQLAlchemy,
        а также возвращает путь к сохраненному изображению
        """
        file_path = f"img/{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{self.user_id}.jpg"
        image.save(file_path)
        return file_path

    def file_exists(self, file: ImageBase) -> bool:
        """
        Валидация успешного сохранения изображения в БД и на диске
        """
        return file.id is not None and os.path.exists(file.image_path)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    """
    Обработка команды /start.
    Функция отправляет в чат приветственное сообщение, указанное в .env
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = types.KeyboardButton("Начать")
    markup.add(start_button)
    bot.send_message(message.chat.id, welcome_phrase, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Начать")
def start_again(message):
    """
    Обработка повторного нажатия кнопки Начать
    """
    bot.send_message(message.chat.id, "Вы уже начали работу с ботом. Загрузите фото")


@bot.message_handler(content_types=["text"])
def echo(message):
    """
    Обработка любого текстового сообщения в виде возврата этого сообщения.
    """
    bot.send_message(message.chat.id, f"Введенный текст: {message.text}")


@bot.message_handler(content_types=["photo"])
def handle_photo(message: Message):
    """
    Основная функция работы с изображением, осуществляющая
    принятие исходного изображения, сохранение измененного
    и его возврат пользователю с предложением поделиться.
    """
    user_image = UserImage(message)

    image_path = bot.get_file(user_image.id).file_path
    downloaded_image = bot.download_file(image_path)

    signed_image = user_image.sign_image(picture_bytes=downloaded_image)
    saved_image_path = user_image.save_image(image=signed_image)

    data = ImageBase(image_id=user_image.id, image_path=saved_image_path)
    session.add(data)
    session.commit()

    if not user_image.file_exists(data):
        bot.send_message(
            message.chat.id,
            "При сохранении файла произошла ошибка",
            reply_to_message_id=message.message_id,
        )
        return

    with open(saved_image_path, "rb") as photo:
        bot.send_photo(message.chat.id, photo=photo)

    markup = types.InlineKeyboardMarkup(row_width=1)
    button_share = types.InlineKeyboardButton("Поделиться", callback_data=f"share_{data.id}")
    markup.add(button_share)

    bot.send_message(
        message.chat.id,
        "Поделитесь новым изображением, если оно Вам понравилось!",
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("share_"))
def share_image(call):
    """
    Функция обработки нажатия кнопки Поделиться, осуществляющая отправление
    измененного изображения в указанный канал (если id канала указано в .env),
    либо в текущий чат.
    """
    db_id_record = int(call.data.split("_")[-1].strip())
    query = select(ImageBase.image_path).where(ImageBase.id == db_id_record)
    image_path = session.scalar(query)

    if image_path:

        resend_id_chat = call.message.chat.id
        if int(os.getenv("RESEND_ID_CHAT")):
            resend_id_chat = os.getenv("RESEND_ID_CHAT")

        with open(image_path, "rb") as photo:
            bot.send_photo(resend_id_chat, photo)
        bot.answer_callback_query(call.id)

    else:
        bot.answer_callback_query(call.id, text="Изображение не найдено")


bot.polling(none_stop=True)
