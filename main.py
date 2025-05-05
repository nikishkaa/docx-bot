import telebot

bot = telebot.TeleBot('7373495523:AAEge_21E9927fNFa9ETnEKknc437cGM4JU')


@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id, f'Hello, {message.from_user.first_name}')


bot.polling(non_stop=True)
