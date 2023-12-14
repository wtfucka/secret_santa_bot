import logging
import os
import random
import sys
import sqlite3
from pprint import pprint

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import (ApplicationBuilder,
                          CommandHandler,
                          CallbackContext,
                          CallbackQueryHandler,
                          filters,
                          MessageHandler)

load_dotenv()

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
FLAGS = {
    'waiting_for_name': True,
    'waiting_for_address': True,
    'waiting_for_phone': True,
    'waiting_for_other_info': True,
}

bot = Bot(token=TELEGRAM_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()


def get_keybord() -> InlineKeyboardMarkup:
    button_join = InlineKeyboardButton(
        'Участвовать',
        callback_data='join',
    )
    button_edit_profile = InlineKeyboardButton(
        'Изменить данные',
        callback_data='edit',
    )
    button_user_list = InlineKeyboardButton(
        'Список участников',
        callback_data='user_list',
    )
    keyboard = InlineKeyboardMarkup(
        [[button_join, button_edit_profile],
         [button_user_list]]
    )
    return keyboard


def get_keybord_for_edit_button() -> InlineKeyboardMarkup:
    button_fio = InlineKeyboardButton(
        'Изменить ФИО',
        callback_data='test1',
    )
    button_address = InlineKeyboardButton(
        'Изменить адрес',
        callback_data='test12',
    )
    button_phone = InlineKeyboardButton(
        'Изменить номер',
        callback_data='test13',
    )
    button_other_info = InlineKeyboardButton(
        'Изменить допинфо',
        callback_data='test4',
    )
    button_all_data = InlineKeyboardButton(
        'Изменить все данные',
        callback_data='join',
    )
    keyboard = InlineKeyboardMarkup(
        [[button_fio, button_address],
         [button_phone, button_other_info],
         [button_all_data]]
    )
    return keyboard


# Обработчик команды /start
async def start(update: Update, context: CallbackContext) -> None:
    """
    Обработка команды "/start".
    """
    user = update.message.from_user
    await update.message.reply_text(
        f'Привет, {user.first_name}! Выбери кнопку:',
        reply_markup=get_keybord()
    )


# Обработчик команды /join
async def join(update: Update, context: CallbackContext) -> None:
    """
    Обработка кнопки "Участвовать" и "Изменить данные".
    """
    query = update.callback_query
    chat_id = update.effective_message.chat_id
    action_type = update.effective_message.text
    await query.answer()
    if action_type == 'Какие данные хочешь изменить?':
        context.user_data['update_all_data'] = True
        await query.edit_message_text(
            text='Введи новые данные.')
    else:
        await query.edit_message_text(
            text=f'{update.effective_chat.first_name}, чтобы присоединиться,'
            ' отправьте свои ФИО, адрес и номер телефона, каждое отдельным'
            ' сообщением.\nНапример:\nИванов Илья Васильевич\nг. Мадрид,'
            'ул. Имени Короля, д. 1, кв. 1\n790000000000.')
    await bot.send_message(chat_id=chat_id, text='Введи ФИО:')
    context.user_data['waiting_for_name'] = True


async def handle_user_input(update: Update, context: CallbackContext) -> None:
    """
    Забираем ответы пользователя для внесения их в БД,
    при нажатии на кнопку "Участвовать". Во всех остальных случаях сообщения
    не учитываются.
    """
    chat_id = update.message.chat_id
    user_input = update.effective_message.text.strip()

    # тут проблема с циклом, рефакторинг дело благое, но не быстрое :D
    # for key, value in FLAGS.items():
    #     # user_input = update.effective_message.text.strip()
    #     if key == 'waiting_for_name' and value:
    #         full_name = update.effective_message.text.strip()
    #         # full_name = user_input
    #         FLAGS[key] = False
    #         await bot.send_message(chat_id=chat_id,
    #                                text='Теперь введи свой адрес:')
    #     elif key == 'waiting_for_address' and value:
    #         address = update.effective_message.text.strip()
    #         # address = user_input
    #         FLAGS[key] = False
    #         await bot.send_message(chat_id=chat_id,
    #                                text='Осталось ввести номер телефона:')
    #     elif key == 'waiting_for_phone' and value:
    #         phone = update.effective_message.text.strip()
    #         # phone = user_input
    #         FLAGS[key] = False
    #         await bot.send_message(chat_id=chat_id,
    #                                text='Если хочешь ещё что-то добавить:')
    #     elif key == 'waiting_for_other_info' and value:
    #         other_info = update.effective_message.text.strip()
    #         # other_info = user_input
    #         FLAGS[key] = False
    #         # await bot.send_message(chat_id=chat_id,
    #         #                        text='Теперь введи свой адрес:')

    # старая реализация, но рабочая
    if context.user_data.get('waiting_for_name', False):
        context.user_data['full_name'] = user_input
        context.user_data['waiting_for_name'] = False
        context.user_data['waiting_for_address'] = True
        # await update.message.reply_text()
        await bot.send_message(chat_id=chat_id,
                               text='Теперь введи свой адрес:')
    elif context.user_data.get('waiting_for_address', False):
        context.user_data['address'] = user_input
        context.user_data['waiting_for_address'] = False
        context.user_data['waiting_for_phone'] = True
        # await update.message.reply_text()
        await bot.send_message(chat_id=chat_id,
                               text='Осталось ввести номер телефона:')
    elif context.user_data.get('waiting_for_phone', False):
        context.user_data['phone'] = user_input
        context.user_data['waiting_for_phone'] = False
        context.user_data['waiting_for_other_info'] = True
        # await update.message.reply_text()
        await bot.send_message(chat_id=chat_id,
                               text='Если хочешь ещё что-то добавить:')
    elif context.user_data.get('waiting_for_other_info', False):
        context.user_data['other_info'] = user_input
        context.user_data['waiting_for_other_info'] = False

    if context.user_data.get('update_all_data', False):
        return await update_data_on_db(update, context)

    return await write_data_to_db(update, context)


async def write_data_to_db(update: Update, context: CallbackContext):
    """
    Записываем полученные данные в БД.
    """
    user_name = update.effective_chat.first_name
    chat_id = update.message.chat_id
    full_name = context.user_data.get('full_name')
    address = context.user_data.get('address')
    phone = context.user_data.get('phone')
    other_info = context.user_data.get('other_info', '')

    if all([full_name, address, phone, other_info]):
        try:
            with sqlite3.connect('secret_santa.db') as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    INSERT INTO users (
                            chat_id,
                            full_name,
                            address,
                            phone_number,
                            other_info
                            )
                    VALUES (?, ?, ?, ?, ?)
                ''', (chat_id,
                      full_name,
                      address,
                      phone,
                      other_info)
                    )
                connection.commit()
            await update.message.reply_text(
                f'Всё отлично {user_name}, ты стал участником!'
            )
            await update.message.reply_text(
                'Выбери кнопку:', reply_markup=get_keybord()
            )
        except sqlite3.Error as error:
            logger.error(f'Проблема с записью данных в БД: {error}')
            await update.message.reply_text(
                'Что-то пошло не так, попробуй еще раз'
            )


async def update_data_on_db(update: Update, context: CallbackContext):
    """
    Записываем полученные данные в БД.
    """
    user_name = update.effective_chat.first_name
    chat_id = update.message.chat_id
    full_name = context.user_data.get('full_name')
    address = context.user_data.get('address')
    phone = context.user_data.get('phone')
    other_info = context.user_data.get('other_info')

    # if not full_name:
    #     query = (f'UPDATE users SET full_name = {full_name} '
    #              f'where chat_id = {chat_id}')
    # if not address:
    #     query = (f'UPDATE users SET address = {address} '
    #              f'where chat_id = {chat_id}')
    # if not phone:
    #     query = (f'UPDATE users SET phone = {phone} '
    #              f'where chat_id = {chat_id}')
    # if not other_info:
    #     query = (f'UPDATE users SET other_info = {other_info} '
    #              f'where chat_id = {chat_id}')

    # if context.user_data.get('update_all_data', False):
    #     query = (
    #         f'UPDATE users '
    #         f'SET full_name = {full_name}, '
    #         f'address = {address}, '
    #         f'phone_number = {phone}, '
    #         f'other_info = {other_info} '
    #         f'WHERE chat_id = {chat_id}')

    update_values = []
    if full_name:
        update_values.append("full_name = ?")
    if address:
        update_values.append("address = ?")
    if phone:
        update_values.append("phone_number = ?")
    if other_info:
        update_values.append("other_info = ?")

    update_values_str = ', '.join(update_values)
    query = f'UPDATE users SET {update_values_str} WHERE chat_id = ?'
    values = [full_name, address, phone, other_info, chat_id]

    try:
        with sqlite3.connect('secret_santa.db') as connection:
            cursor = connection.cursor()
            cursor.execute(query, values)
            connection.commit()
        await update.message.reply_text(
            f'Всё отлично {user_name}, данные изменены!'
        )
        await update.message.reply_text(
            'Выбери кнопку:', reply_markup=get_keybord()
        )
    except sqlite3.Error as error:
        logger.error(f'Проблема с записью данных в БД: {error}')
        await update.message.reply_text(
            'Что-то пошло не так, попробуй еще раз.'
        )


# Обработчик команды /edit
async def edit(update: Update, context: CallbackContext) -> None:
    """
    Обработка кнопки "Изменить данные".
    """
    query = update.callback_query
    chat_id = update.effective_message.chat_id
    await query.answer()
    await query.edit_message_text(
        text='Какие данные хочешь изменить?',
        reply_markup=get_keybord_for_edit_button())
    # await bot.send_message(chat_id=chat_id, text='Введи ФИО:')


# Обработчик команды /list
async def users_count_first_ten_users(update: Update,
                                      context: CallbackContext) -> None:
    """
    Обработка кнопки "Список участников".
    Выводит общее количество и первые 10 ФИО участников.
    """
    button_view_all_users = InlineKeyboardButton(
        'Посмотреть всех',
        callback_data='all_participants',
    )
    keyboard = InlineKeyboardMarkup(
        [[button_view_all_users]]
    )
    chat_id = update.effective_message.chat_id
    query = update.callback_query
    await query.answer()
    total_users = get_total_users()
    users_list = get_users_list()
    message_text = '\n'.join(users_list[:10])
    await bot.send_message(
        chat_id=chat_id,
        text=f'Общее количество участников: {total_users}'
    )
    await bot.send_message(
        chat_id=chat_id,
        text=f'Список участников (будут показаны первые 10):\n{message_text}',
        reply_markup=keyboard
    )


async def get_participants_list(update: Update, context: CallbackContext):
    """
    Обработка кнопки "Посмотреть всех". Кнопка доступна только из метода
    "users_count_first_ten_users".
    """
    chat_id = update.effective_message.chat_id
    users_list = get_users_list()
    message_text = '\n'.join(users_list)
    await bot.send_message(
        chat_id=chat_id,
        text=f'Список всех участников:\n{message_text}'
    )


def get_total_users():
    """
    Метод для подсчета количества участников.
    """
    with sqlite3.connect('secret_santa.db') as connection:
        try:
            cursor = connection.cursor()
            query = cursor.execute('''
                select count(*) from users;
            ''')
            total_users = query.fetchone()[0]
        except sqlite3.Error as error:
            logger.error(f'Проблема с получением данных из БД: {error}')
    return total_users


def get_users_list():
    """
    Метод для вывода списка участников.
    """
    with sqlite3.connect('secret_santa.db') as connection:
        try:
            cursor = connection.cursor()
            query = cursor.execute('''
                select full_name from users;
            ''')
            user_list = [user[0] for user in query.fetchall()]
        except sqlite3.Error as error:
            logger.error(f'Проблема с получением данных из БД: {error}')
    return user_list


# Обработчик команды /assign
async def assign(update: Update, context: CallbackContext) -> None:
    """
    Метод для распределения участников по парам в назначенное время.
    """
    list_of_participants = 'select id from users'
    list_of_santas = secret_santa_algorithm(list_of_participants)

    list_of_persons = get_list_persons()
    for person in list_of_persons:
        full_name, address, phone = person
        for chat_id, full_name in list_of_chats.items():
            await bot.send_message(
                chat_id=chat_id,
                text=('Распределение участников завершено.\n'
                      f'Тебе нужно сделать подарок для - {full_name}.\n'
                      f'Отправить подарок можно по адресу - {address}.\n'
                      'Если нужно что-то уточнить у одариваемого, '
                      f'то вот номер - {phone}')
                )


def write_santas_to_db(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    query = f'UPDATE users SET assigned_user_id WHERE chat_id = ?'
    try:
        with sqlite3.connect('secret_santa.db') as connection:
            cursor = connection.cursor()
            cursor.execute(query, chat_id)
            connection.commit()


def secret_santa_algorithm(participants):
    if len(participants) % 2 != 0:
        participants.append('Фиктивный участник')
        fake_santa = None
        fake_reciever = None

    random.shuffle(participants)
    santa_pairs = {participants[i]: participants[(i + 1) % len(participants)] for i in range(len(participants))}

    for santa, receiver in santa_pairs.items():
        if santa == 'Фиктивный участник':
            fake_reciever = receiver
            fake_santa_key = santa
        if receiver == 'Фиктивный участник':
            fake_santa = santa
            fake_receiver_key = santa

    del santa_pairs[fake_santa_key]
    del santa_pairs[fake_receiver_key]
    santa_pairs[fake_santa] = fake_reciever

    return santa_pairs


# Инициализация бота
def main() -> None:

    # Регистрация обработчиков команд
    application.add_handlers(
        handlers=(CommandHandler('start', start),
                  CommandHandler('join', join),
                  CallbackQueryHandler(join, 'join'),
                  MessageHandler(filters.TEXT, callback=handle_user_input),
                  CommandHandler('user_list', users_count_first_ten_users),
                  CallbackQueryHandler(users_count_first_ten_users,
                                       'user_list'),
                  CommandHandler('all_participants', get_participants_list),
                  CallbackQueryHandler(get_participants_list,
                                       'all_participants'),
                  CommandHandler('edit', edit),
                  CallbackQueryHandler(edit, 'edit'),
                #   CommandHandler('assign', assign)
                  )
                )

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    # создаем логгер
    logging.basicConfig(
        level=logging.INFO,
        filename='secret_santa.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(funcName)s',
        encoding='utf-8'
    )

    main()
