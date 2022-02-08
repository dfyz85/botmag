import logging
from typing import Dict
import uuid

from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove, Message,InputMediaVideo, InputMediaPhoto, InputMediaDocument, InputMediaAudio
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CommandHandler,
)
from telegram.utils.helpers import effective_message_type

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE, TYPING_CONTACT, TYPING_DOP = range(5)

reply_keyboard = [
    ['Как в вам обращаться','Должность', 'Судно'],
    ['Описание проблемы', 'Доп. материалы'],
    ['Контакты для связи', 'Тип помощи','Отпарвить'],
]
contact_keyboard = [
    ['Назад к проблеме'],
    ['e-mail'],
    ['телефон'],
    ['WhatsApp'],
    ['Telegram'],
    ['Viber']
]
problem_keyboard = [
    ['Назад к проблеме'],
    ['Двигатель','Генератор','Автоматика'],
    ['Котел','Сепаратор','Fire system'],
    ['Система кондиционирования', 'Нет в списке']
]
problem_keyboard = [
    ['Переписка','Разговор'],
    ['Назад к проблеме']
]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f'{key} - {value}' for key, value in user_data.items()]
    filter_facts = list(filter(lambda score: 'Dop_file' not in score ,facts))
    return "\n".join(filter_facts)

def start(update: Update, context: CallbackContext) -> int:
    message = update.effective_message
    """Start the conversation and ask user for input."""
    try:
        login = context.user_data['login']
    except Exception as e:
        login = 'колега'
    update.message.reply_text(
        f"""Добрый день {login}!
Вы воспользовались системой технической потдержки MAGwaters для любого вида судов.
Для оформления заявки заполните нужные поля и нажмите "Отправить".
Доп. материалы размеры одного файла не должны привышать 20 MB.""",
        reply_markup=markup,
    )
    context.bot.delete_message(message.chat_id, message.message_id)
    return CHOOSING

def regular_choice(update: Update, context: CallbackContext) -> int:
    """Ask the user for info about the selected predefined choice."""
    message = update.effective_message
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(f'Укажите {text.capitalize()}.')
    context.bot.delete_message(message.chat_id, message.message_id)
    return TYPING_REPLY

def custom_choice(update: Update, context: CallbackContext) -> int:
    """Ask the user for a description of a custom category."""
    update.message.reply_text(
        'Alright, please send me the category first, for example "Most impressive skill"'
    )
    return TYPING_CHOICE

def received_information(update: Update, context: CallbackContext) -> int:
    """Store info provided by user and ask for the next category."""
    message = update.effective_message
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']
    # del user_data['login']
    update.message.reply_text(
        f"""Для информации вы указали следущию информацию:
{facts_to_str(user_data)}
Укажите больше или измените если ошиблись.
Для завершения заявки нашмите "Отправить" """,
        reply_markup=markup,
    )
    context.bot.delete_message(message.chat_id, message.message_id)
    return CHOOSING

def done(update: Update, context: CallbackContext) -> int:
    chat = '-1001698024013'
    id = uuid.uuid4()
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']
    if 'login' in user_data:
        del user_data['login']
    update.message.reply_text(
        f"Следующая заявка сформирована:\nID:{id}\n{facts_to_str(user_data)}\nСпасибо Мы свяжимся с вами в ближайшее время!",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.bot.send_message(chat, f"Ticket {id}: {facts_to_str(user_data)}")
    print(user_data)
    if 'Dop_file' in user_data:
        dop_files = user_data['Dop_file'].split()
        print(dop_files)
        for dop_file in dop_files:
            # context.bot.send_document(chat, dop_file)
            context.bot.copy_message(chat, update.message.chat_id, dop_file)
        del user_data['Dop_file']
    user_data.clear()
    return ConversationHandler.END

def login(update: Update, context: CallbackContext) -> None:
    context.user_data['login'] = update.message.text
    update.message.reply_text(update.message.text)

def contact_choice(update: Update, context: CallbackContext) -> int:
    message = update.effective_message
    update.message.reply_text(
        f"Добавте контактную информацию для обратной связи:",
        reply_markup=ReplyKeyboardMarkup(contact_keyboard, one_time_keyboard=True),
    )
    context.bot.delete_message(message.chat_id, message.message_id)
    return TYPING_CONTACT

def contact_recive(update: Update, context: CallbackContext) -> int:
    message = update.effective_message
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(f'Укажите ваш {text.lower()}')
    context.bot.delete_message(message.chat_id, message.message_id)
    return TYPING_REPLY

def back_to_main_choice(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    update.message.reply_text(
         f"""Для информации вы указали следущию информацию
{facts_to_str(user_data)}
Укажите больше или измените если ошиблись.
Для завершения заявки нашмите "Отправить" """,
        reply_markup=markup,
    )
    return CHOOSING

def help_choice(update: Update, context: CallbackContext) -> int:
    message = update.effective_message
    text = update.message.text
    context.user_data['choice'] = text 
    update.message.reply_text(
        f"Добавте контактную информацию для обратной связи:",
        reply_markup=ReplyKeyboardMarkup(problem_keyboard, one_time_keyboard=True),
    )
    context.bot.delete_message(message.chat_id, message.message_id)
    return TYPING_REPLY

def problem_choice(update: Update, context: CallbackContext) -> int:
    message = update.effective_message
    text = update.message.text
    context.user_data['choice'] = text 
    update.message.reply_text(
        f"Добавте контактную информацию для обратной связи:",
        reply_markup=ReplyKeyboardMarkup(problem_keyboard, one_time_keyboard=True),
    )
    context.bot.delete_message(message.chat_id, message.message_id)
    return TYPING_REPLY

def dop_choice(update: Update, context: CallbackContext) -> int:
    message = update.effective_message
    text = update.message.text
    context.user_data['choice'] = text 
    update.message.reply_text(
        f"Добавте фото или мануал который поможет быстрее решить проблему",
        reply_markup=ReplyKeyboardMarkup([], input_field_placeholder='Добавте документ', one_time_keyboard=True)
    )
    context.bot.delete_message(message.chat_id, message.message_id)
    return TYPING_DOP

def dop_recive(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    #Download photo
    # file_data = update.message.photo[-1].get_file()
    # file_data.download('photo.jpg')
    # Download file
    # file_data = update.message.message_id.get_file()
    # file_data.download(update.message.document.file_name)
    user_data = context.user_data
    try:
        user_data['Dop_file'] = f"{user_data['Dop_file']} {message.message_id}"
    except Exception as e:
        user_data['Dop_file'] = message.message_id
    update.message.reply_text(
        f"Файл добавлен!",
        reply_markup=markup
    )
    return TYPING_DOP

def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("5013769914:AAHy0-qm-TxsdCPSyKGxrMXJqrfGszZgkrg")
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(
                    Filters.regex('^(Как в вам обращаться|Должность|Судно|Описание проблемы)$'), 
                    regular_choice
                ),
                MessageHandler(
                    Filters.regex('^Контакты для связи$'), 
                    contact_choice
                ),
                MessageHandler(
                    Filters.regex('^Тип помощи$'), 
                    help_choice
                ),
                MessageHandler(
                    Filters.regex('^Доп. материалы$'), 
                    dop_choice
                ),
                MessageHandler(
                    Filters.regex('^Отпарвить$'), 
                    done
                ),
                MessageHandler(
                    Filters.regex('.*'), 
                    back_to_main_choice
                ),
                # MessageHandler(Filters.regex('^Something else...$'), custom_choice),
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Отпарвить$')), 
                    regular_choice
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Отпарвить$')),
                    received_information,
                )
            ],
            TYPING_CONTACT: [
                MessageHandler(
                    Filters.regex('^(e-mail|телефон|WhatsApp|Telegram|Viber)$'), 
                    contact_recive,
                ),
                MessageHandler(
                    Filters.regex('^Назад к проблеме$'), 
                    back_to_main_choice,
                ),
                MessageHandler(
                    Filters.regex('.*'), 
                    back_to_main_choice
                ),
            ],
            TYPING_DOP:[
                MessageHandler(
                    Filters.document, 
                    dop_recive,
                ),
                MessageHandler(
                    Filters.photo, 
                    dop_recive,
                ),
                MessageHandler(
                    Filters.video, 
                    dop_recive,
                ),
                MessageHandler(
                    Filters.regex('^(Как в вам обращаться|Должность|Судно|Описание проблемы)$'), 
                    regular_choice
                ),
                MessageHandler(
                    Filters.regex('^Проблема$'), 
                    regular_choice
                ),
                MessageHandler(
                    Filters.regex('^Контакты для связи$'), 
                    contact_choice
                ),
                MessageHandler(
                    Filters.regex('^Тип помощи$'), 
                    help_choice
                ),
                MessageHandler(
                    Filters.regex('^Доп. материалы$'), 
                    dop_choice
                ),
                MessageHandler(
                    Filters.regex('^Отпарвить$'), 
                    done
                ),
                MessageHandler(
                    Filters.regex('.*'), 
                    back_to_main_choice
                ),
            ]
        },
        fallbacks=[MessageHandler(Filters.regex('^Отпарвить$'), done)],
    )
    dispatcher.add_handler(CommandHandler('login', login))
    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()