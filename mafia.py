from telebot import TeleBot
import db
from time import sleep

TOKEN = '8890416107:AAGwEGfzzcWImT-4M1DmrNCC7eR7VFI-aNg'
bot = TeleBot(TOKEN)

game = False
night = False

@bot.message_handler(commands=['play', 'game'])
def play(message):
    bot.send_message(message.chat.id, 'Если хотите играть, напишите "готов играть" в личные сообщения')
    
@bot.message_handler(func= lambda m: m.text.lower() == 'готов играть' and m.chat.type == 'private')
def send_text(message):
    bot.send_message(message.chat.id, f'{message.from_user.first_name} играет')
    bot.send_message(message.chat.id, 'Вы добавлены в игру')
    db.insert_player(player_id=message.from_user.id, username=message.from_user.first_name)


@bot.message_handler(command = ['game'])
def game_start(message):
    global game

    players = db.players_amount()
    if players >= 5 and not game:
        db.set_roles(players)
        players_roles = db.get_players_roles()
        mafia_usernames = db.get_mafia_username()

        for player_id, role in players_roles:
            bot.send_message(player_id, text=f"Твоя роль: {role}")
            if role == 'mafia':
                bot.send_message(player_id, text = f"Мафии:\n{mafia_usernames}")
        game = True
        bot.send_message(message.chat.id, text='Игра началась!')
    elif players < 5 :
        bot.send_message(message.chat.id, text='Недостаточно людей! (нужно минимум 5)')
    elif game:
        bot.send_message(message.chat.id, text='Игра уже идет!')

@bot.message_handler(commands=['kick'])
def kick(message):
    global night
    username = ' '.join(message.text.split()[1:])
    usernames = db.get_all_alive()
    if not night:
        if not username in usernames:
            bot.send_message(message.chat.id, 'Такого играка нет в живых')
            return

        voted = db.vote('citizen_vote', username, message.from_user.id)
        if voted:
            bot.send_message(message.chat.id, 'Ваш голос учтен')
            return

        bot.send_message(message.chat.id, 'Вы больше не можете голосовать')
        return
    bot.send_message(message.chat.id, 'Сейчас ночь, вы не можете голосовать')

@bot.message_handler(commands=['kill'])
def kill(message):
    global night
    username = ' '.join(message.text.split()[1:])
    usernames = db.get_all_alive

    names = db.get_mafia_username()
    if message.from_user.first_name in names:
        if night:
            if not username in usernames:
                bot.send_message(message.chat.id, 'Такого играка нет в живых')
                return

            voted = db.vote('mafia_vote', username, message.from_user.id)
            if voted:
                bot.send_message(message.chat.id, f'Ваш голос за {username} учтен')
                return
            
            bot.send_message(message.chat.id, 'Вы больше не можете голосовать')
            return
        bot.send_message(message.chat.id, 'Сейчас день, вы не можете голосовать')
        return
    bot.send_message(message.chat.id, 'Вы не мафия, вы не можете убить')

def get_killed(night):
    if not night:
        username_killed = db.citizens_kill()
        return f"Горожане выгнали: {username_killed}"
    username_killed = db.mafia_kill()
    return f"Мафия убила: {username_killed}"

night = True

def game_loop(message):
    global night, game
    bot.send_message(message.chat.id, "Добро пожаловать в игру. У вас есть две минуты чтобы познакомиться")
    sleep(120)
    while True:

        if night:
            bot.send_message(message.chat.id, "Город засыпаетю, просыпается мафия. Наступила ночь")
        else:
            bot.send_message(message.chat.id, "Город просыпается. Наступил день.")

        if night:
            sleep(60)
            killed = db.mafia_kill()
        else:
            bot.send_message(message.chat.id, "У вас есть минута чтобы проголосовать")
            sleep(60)
            killed = db.citizens_kill()

        if killed != "никого":
            bot.send_message(message.chat.id, f"Выбыл игрок: {killed}")

        winner = db.check_winner()
        if winner:
            bot.send_message(message.chat.id, f"Игра окончена. Выйграла {winner}")
            game = False
            db.clear(dead=False)
            break

        night = not night
        alive = db.get_all_alive()
        alive = '\n'.join(alive)
        bot.send_message(message.chat.id, f"В игре: \n {alive}")
        sleep(2)
            
            


bot.polling(none_stop=True)

