import telebot
from flask import Flask, request
import os
import logging
import requests
import time
import messages as responses

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

API_TOKEN = os.environ.get('TOKEN')

bot = telebot.TeleBot(API_TOKEN, parse_mode='HTML')
server = Flask(__name__)


def get_siu_info():
    siu_data = dict()
    t0 = time.time()
    r = requests.get('https://autogestion.uno.edu.ar/uno/')
    t1 = time.time()
    siu_data['status'] = r.status_code
    siu_data['latency'] = int((t1-t0) * 1000)
    return siu_data


def get_links_from_api():
    res = requests.get('https://igna98.alwaysdata.net/page')
    data = res.json()['data']
    mapped_list = list(map(lambda link: link['name'], data))
    return responses.links_message(mapped_list)


def siu_message():
    siu_data = get_siu_info()
    if siu_data['status'] == 200:
        return responses.siu_success_message(siu_data['latency'])
    else:
        return responses.siu_failure_message(siu_data['latency'])


def get_links_message():
    return get_links_from_api()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, "Bienvenidx a este botardo con información util sobre la Universidad Nacional del Oeste. Escribí <b>/help</b> para saber cómo seguir.")


@bot.message_handler(commands=['help'])
def help_message(message):
    user_id = message.from_user.id
    logger.info(f"El usuario {user_id} ha solicitado AYUDA.")
    chat_id = message.chat.id
    bot.send_message(chat_id, responses.help_message())


@bot.message_handler(commands=['links'])
def get_useful_links(message):
    user_id = message.from_user.id
    logger.info(f"El usuario {user_id} ha solicitado LINKS.")
    chat_id = message.chat.id
    bot.send_message(chat_id, get_links_message())


@bot.message_handler(commands=['siu'])
def request_siu_information(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    logger.info(f"El usuario {user_id} ha solicitado información del SIU.")
    bot.send_message(
        chat_id, f"<i>Solicitando información a https://autogestion.uno.edu.ar/uno/ ...</i>")
    bot.send_message(
        chat_id, siu_message())


@bot.message_handler(commands=['calendar'])
def get_academic_calendar(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    logger.info(f"El usuario {user_id} ha solicitado el Calendario Academico.")
    bot.send_message(chat_id, responses.calendario_academico_message())


@bot.message_handler(commands=['mails'])
def get_emails(message):
    arguments = message.text.split()
    user_id = message.from_user.id
    chat_id = message.chat.id
    logger.info(f"El usuario {user_id} ha solicitado MAILS.")
    if len(arguments) > 1:
        bot.send_message(chat_id, responses.get_mails_by_term(arguments[1]))
    else:
        bot.send_message(chat_id, responses.get_mails_by_term())


@server.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates(
        [telebot.types.Update.de_json(request.stream.read().decode('utf-8'))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=os.environ.get('URL_NAME') + API_TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
