import datetime
import logging
import os
import random
import sqlite3

import telegram.error
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

X_DATE = datetime.datetime(2023, 12, 30)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID'))

bot = Bot(token=TELEGRAM_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()


def get_admin_keybord() -> InlineKeyboardMarkup:
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
    button_sending_messages = InlineKeyboardButton(
        'Распределение и отправка сообщений',
        callback_data='x_moment',
    )
    keyboard = InlineKeyboardMarkup(
        [[button_join, button_edit_profile],
         [button_user_list],
         [button_sending_messages]]
    )
    return keyboard


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
        callback_data='change_name',
    )
    button_address = InlineKeyboardButton(
        'Изменить адрес',
        callback_data='change_address',
    )
    button_phone = InlineKeyboardButton(
        'Изменить номер',
        callback_data='change_phone',
    )
    button_other_info = InlineKeyboardButton(
        'Изменить допинфо',
        callback_data='change_other_info',
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
    try:
        if user.id == ADMIN_CHAT_ID:
            await update.message.reply_text(
                f'Привет, {user.first_name}! Выбери кнопку:',
                reply_markup=get_admin_keybord()
            )
        else:
            await update.message.reply_text(
                f'Привет, {user.first_name}! Выбери кнопку:',
                reply_markup=get_keybord()
            )
    except telegram.error as error:
        logger.critical(f'Что-то пошло не так: {error}')


# Обработчик команды /join
async def join(update: Update, context: CallbackContext) -> None:
    """
    Обработка кнопки "Участвовать" и "Изменить данные".
    """
    query = update.callback_query
    chat_id = update.effective_user.id
    action_type = update.effective_message.text
    try:
        await query.answer()
        if action_type == 'Какие данные хочешь изменить?':
            context.user_data['update_all_data'] = True
            await query.edit_message_text(
                text='Введи новые данные.')
        else:
            await query.edit_message_text(
                text=f'{update.effective_chat.first_name}, чтобы '
                'присоединиться, отправьте свои ФИО, адрес и номер телефона, '
                'каждое отдельным сообщением.\nНапример:\nИванов Илья '
                'Васильевич\nг. Мадрид,ул. Имени Короля, д. 1, кв. 1'
                '\n790000000000.')
        await bot.send_message(chat_id=chat_id, text='Введи ФИО:')
        context.user_data['waiting_for_name'] = True
    except telegram.error as error:
        logger.critical(f'Что-то пошло не так: {error}')


async def participant_user_input(update: Update,
                                 context: CallbackContext) -> None:
    """
    Забираем ответы пользователя для внесения их в БД,
    при нажатии на кнопку "Участвовать" или "Изменить все данные".
    Во всех остальных случаях сообщения не учитываются.
    """
    chat_id = update.effective_user.id
    user_input = update.effective_message.text.strip()

    # Если выбрали частичное обновление данных
    if context.user_data.get('partial_update', False):
        if context.user_data.get('waiting_for_name', False):
            context.user_data['full_name'] = user_input
            context.user_data['waiting_for_name'] = False

        if context.user_data.get('waiting_for_address', False):
            context.user_data['address'] = user_input
            context.user_data['waiting_for_address'] = False

        if context.user_data.get('waiting_for_phone', False):
            context.user_data['phone'] = user_input
            context.user_data['waiting_for_phone'] = False

        if context.user_data.get('waiting_for_other_info', False):
            context.user_data['other_info'] = user_input
            context.user_data['waiting_for_other_info'] = False

        return await update_data_on_db(update, context)

    # Если выбрали новое участие или полное обновление данных
    if context.user_data.get('waiting_for_name', False):
        context.user_data['full_name'] = user_input
        context.user_data['waiting_for_name'] = False
        context.user_data['waiting_for_address'] = True
        await bot.send_message(chat_id=chat_id,
                               text='Теперь введи свой адрес:')
    elif context.user_data.get('waiting_for_address', False):
        context.user_data['address'] = user_input
        context.user_data['waiting_for_address'] = False
        context.user_data['waiting_for_phone'] = True
        await bot.send_message(chat_id=chat_id,
                               text='Осталось ввести номер телефона:')
    elif context.user_data.get('waiting_for_phone', False):
        context.user_data['phone'] = user_input
        context.user_data['waiting_for_phone'] = False
        context.user_data['waiting_for_other_info'] = True
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
    chat_id = update.effective_user.id
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
            try:
                await update.message.reply_text(
                    f'Всё отлично {user_name}, ты стал участником!'
                )
                await update.message.reply_text(
                    'Выбери кнопку:', reply_markup=get_keybord()
                )
            except telegram.error as tg_error:
                logger.critical(f'Что-то пошло не так: {tg_error}')
        except sqlite3.Error as error:
            logger.error(f'Проблема с записью данных в БД: {error}')
            try:
                if str(error).startswith('UNIQUE constraint failed'):
                    await update.message.reply_text(
                        'Дважды стать участником не получится.'
                    )
                else:
                    await update.message.reply_text(
                        'Что-то пошло не так, попробуй еще раз'
                    )
            except telegram.error as tg_error:
                logger.critical(f'Что-то пошло не так: {tg_error}')
        finally:
            context.user_data.clear()


async def update_data_on_db(update: Update, context: CallbackContext):
    """
    Записываем полученные данные в БД.
    """
    user_name = update.effective_chat.first_name
    chat_id = update.effective_user.id
    full_name = context.user_data.get('full_name')
    address = context.user_data.get('address')
    phone = context.user_data.get('phone')
    other_info = context.user_data.get('other_info')

    update_values = []
    values = []
    if full_name:
        update_values.append("full_name = ?")
        values.append(full_name)
    if address:
        update_values.append("address = ?")
        values.append(address)
    if phone:
        update_values.append("phone_number = ?")
        values.append(phone)
    if other_info:
        update_values.append("other_info = ?")
        values.append(other_info)

    values.append(chat_id)
    update_values_str = ', '.join(update_values)
    query = f'UPDATE users SET {update_values_str} WHERE chat_id = ?'

    try:
        with sqlite3.connect('secret_santa.db') as connection:
            cursor = connection.cursor()
            cursor.execute(query, values)
            connection.commit()
        try:
            await update.message.reply_text(
                f'Всё отлично {user_name}, данные изменены!'
            )
            await update.message.reply_text(
                'Выбери кнопку:', reply_markup=get_keybord()
            )
        except telegram.error as tg_error:
            logger.critical(f'Что-то пошло не так: {tg_error}')
    except sqlite3.Error as error:
        logger.error(f'Проблема с записью данных в БД: {error}')
        await update.message.reply_text(
            'Что-то пошло не так, попробуй еще раз.'
        )
    finally:
        context.user_data.clear()


# Обработчик команды /edit
async def edit(update: Update, context: CallbackContext) -> None:
    """
    Обработка кнопки "Изменить данные".
    """
    query = update.callback_query
    try:
        await query.answer()
        await query.edit_message_text(
            text='Какие данные хочешь изменить?',
            reply_markup=get_keybord_for_edit_button())
    except telegram.error as tg_error:
        logger.critical(f'Что-то пошло не так: {tg_error}')


async def change_name(update: Update, context: CallbackQueryHandler):
    """
    Обработка кнопки "Изменить ФИО".
    """
    query = update.callback_query
    try:
        await query.answer()
        await query.edit_message_text(
            text='Введи ФИО:')
        context.user_data['partial_update'] = True
        context.user_data['waiting_for_name'] = True
    except telegram.error as tg_error:
        logger.critical(f'Что-то пошло не так: {tg_error}')


async def change_address(update: Update, context: CallbackQueryHandler):
    """
    Обработка кнопки "Изменить адресс".
    """
    query = update.callback_query
    try:
        await query.answer()
        await query.edit_message_text(
            text='Введи адрес:')
        context.user_data['partial_update'] = True
        context.user_data['waiting_for_address'] = True
    except telegram.error as tg_error:
        logger.critical(f'Что-то пошло не так: {tg_error}')


async def change_phone(update: Update, context: CallbackQueryHandler):
    """
    Обработка кнопки "Изменить номер".
    """
    query = update.callback_query
    try:
        await query.answer()
        await query.edit_message_text(
            text='Введи телефон:')
        context.user_data['partial_update'] = True
        context.user_data['waiting_for_phone'] = True
    except telegram.error as tg_error:
        logger.critical(f'Что-то пошло не так: {tg_error}')


async def change_other_info(update: Update, context: CallbackQueryHandler):
    """
    Обработка кнопки "Изменить другие данные".
    """
    query = update.callback_query
    try:
        await query.answer()
        await query.edit_message_text(
            text='Введи дополнительную информацию:')
        context.user_data['partial_update'] = True
        context.user_data['waiting_for_other_info'] = True
    except telegram.error as tg_error:
        logger.critical(f'Что-то пошло не так: {tg_error}')


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
    try:
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
            text=('Список участников (будут показаны первые 10):'
                  f'\n{message_text}'),
            reply_markup=keyboard
        )
    except telegram.error as tg_error:
        logger.critical(f'Что-то пошло не так: {tg_error}')


async def get_participants_list(update: Update, context: CallbackContext):
    """
    Обработка кнопки "Посмотреть всех". Кнопка доступна только из метода
    "users_count_first_ten_users".
    """
    chat_id = update.effective_message.chat_id
    users_list = get_users_list()
    message_text = '\n'.join(users_list)
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=f'Список всех участников:\n{message_text}'
        )
    except telegram.error as tg_error:
        logger.critical(f'Что-то пошло не так: {tg_error}')


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
            user_list = query.fetchall()[0]
        except sqlite3.Error as error:
            logger.error(f'Проблема с получением данных из БД: {error}')
    return user_list


# Обработчик команды /assign_santas_recievers
def assign_santas_recievers() -> None:
    """
    Метод для распределения участников по парам в назначенное время.
    """
    with sqlite3.connect('secret_santa.db') as connection:
        try:
            cursor = connection.cursor()
            query = cursor.execute('''
                    select chat_id from users;
                ''')
            list_of_participants = [user[0] for user in query.fetchall()]
        except sqlite3.Error as error:
            logger.error(f'Проблема с получением данных из БД: {error}')

    list_of_santas = secret_santa_algorithm(list_of_participants)

    return write_santas_to_db(list_of_santas)


async def sending_messages(update: Update, context: CallbackContext):
    """
    Метод для рассылки сообщений после распределения участников.
    """
    try:
        with sqlite3.connect('secret_santa.db') as connection:
            cursor = connection.cursor()
            query = cursor.execute('''
                    select
                            chat_id,
                            gift_reciever_full_name,
                            gift_reciever_address,
                            gift_reciever_phone_number,
                            gift_reciever_other_info
                    from users;
                ''')
            for santa in query.fetchall():
                (chat_id,
                 gift_reciever_full_name,
                 gift_reciever_address,
                 gift_reciever_phone_number,
                 gift_reciever_other_info) = santa
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=(
                            'Распределение участников завершено.\n'
                            'Тебе нужно сделать подарок для - '
                            f'{gift_reciever_full_name}.\n'
                            f'Отправить подарок можно по адресу - '
                            f'{gift_reciever_address}.\n'
                            'Если нужно что-то уточнить у одариваемого, '
                            f'то вот номер - {gift_reciever_phone_number}.\n'
                            'А это дополнительная информация, которую он '
                            'оставил, вдруг пригодится - '
                            f'{gift_reciever_other_info}'
                            )
                        )
                except telegram.error as tg_error:
                    logger.critical(f'Что-то пошло не так: {tg_error}')
    except sqlite3.Error as error:
        logger.error(f'Проблема с получением данных из БД: {error}')


def write_santas_to_db(santa_pairs):

    try:
        with sqlite3.connect('secret_santa.db') as connection:
            cursor = connection.cursor()
            for santa, reciever in santa_pairs.items():
                select_query = (f'''select
                                chat_id,
                                full_name,
                                address,
                                phone_number,
                                other_info
                                from users
                                where chat_id = {reciever}
                        ''')
                query = cursor.execute(select_query)
                for reciever_data in query.fetchall():
                    (reciever_chat_id,
                     reciever_full_name,
                     reciever_address,
                     reciever_phone,
                     reciever_other_info) = reciever_data
                    update_query = ('''UPDATE users
                                    SET gift_reciever_chat_id = ?,
                                    gift_reciever_full_name = ?,
                                    gift_reciever_address = ?,
                                    gift_reciever_phone_number = ?,
                                    gift_reciever_other_info = ?
                                    WHERE chat_id = ?
                            ''')
                    update_values = [reciever_chat_id,
                                     reciever_full_name,
                                     reciever_address,
                                     reciever_phone,
                                     reciever_other_info,
                                     santa]
                    query = cursor.execute(update_query, update_values)
            connection.commit()
    except sqlite3.Error as error:
        logger.error(f'Проблема с получением/записью данных в БД: {error}')


def secret_santa_algorithm(participants):
    if len(participants) % 2 != 0:
        participants.append('Фиктивный участник')
        fake_santa = None
        fake_reciever = None

        random.shuffle(participants)
        santa_pairs = {participants[i]: participants[(i + 1) % len(
            participants)] for i in range(len(participants))}

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
    else:
        random.shuffle(participants)
        santa_pairs = {participants[i]: participants[(i + 1) % len(
            participants)] for i in range(len(participants))}
    return santa_pairs


# Инициализация бота
def main() -> None:

    # Регистрация обработчиков команд
    application.add_handlers(
        handlers=(CommandHandler('start', start),
                  CommandHandler('join', join),
                  CallbackQueryHandler(join, 'join'),
                  MessageHandler(filters.TEXT,
                                 callback=participant_user_input),
                  CommandHandler('user_list', users_count_first_ten_users),
                  CallbackQueryHandler(users_count_first_ten_users,
                                       'user_list'),
                  CommandHandler('all_participants', get_participants_list),
                  CallbackQueryHandler(get_participants_list,
                                       'all_participants'),
                  CommandHandler('edit', edit),
                  CallbackQueryHandler(edit, 'edit'),
                  CommandHandler('change_name', change_name),
                  CallbackQueryHandler(change_name, 'change_name'),
                  CommandHandler('change_address', change_address),
                  CallbackQueryHandler(change_address, 'change_address'),
                  CommandHandler('change_phone', change_phone),
                  CallbackQueryHandler(change_phone, 'change_phone'),
                  CommandHandler('change_other_info', change_other_info),
                  CallbackQueryHandler(change_other_info, 'change_other_info'),
                  CommandHandler('x_moment', sending_messages),
                  CallbackQueryHandler(sending_messages, 'x_moment'),
                  )
                )

    # Запуск бота
    try:
        application.run_polling()
        logger.info('Успешный старт')
    except telegram.error as error:
        logger.critical(f'Что-то пошло не так: {error}')

    if datetime.datetime.now() >= X_DATE:
        assign_santas_recievers()


if __name__ == '__main__':
    # настраиваем логгер
    logging.basicConfig(
        level=logging.INFO,
        filename='secret_santa.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(funcName)s',
        encoding='utf-8'
    )

    main()
