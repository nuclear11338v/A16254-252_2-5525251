import telebot
from datetime import datetime, timedelta
import string
import random
from telebot import types
import time
import hashlib
import json

# Bot token
BOT_TOKEN = "7790806618:AAGO0S0raqPU86WE_pRaWnuEUiehV2Jo0hc"
bot = telebot.TeleBot(BOT_TOKEN)


premium_users = {}
admins = [7933339379]
chat_queue = []
active_chats = {}
user_coins = {}
users = set()
users_db = {}
waiting_users = []
tasks = []

def save_data():
    data = {
        "premium_users": premium_users,
        "admins": admins,
        "chat_queue": chat_queue,
        "active_chats": active_chats,
        "user_coins": user_coins,
        "users": list(users),  # Convert set to list for JSON serialization
        "users_db": users_db,
        "waiting_users": waiting_users,
        "tasks": tasks
    }
    with open('backup_data.json', 'w') as file:
        json.dump(data, file)

# Function to load data from a JSON file
def load_data():
    global premium_users, admins, chat_queue, active_chats, user_coins, users, users_db, waiting_users, tasks
    try:
        with open('backup_data.json', 'r') as file:
            data = json.load(file)
            premium_users = data["premium_users"]
            admins = data["admins"]
            chat_queue = data["chat_queue"]
            active_chats = data["active_chats"]
            user_coins = data["user_coins"]
            users = set(data["users"])  # Convert list back to set
            users_db = data["users_db"]
            waiting_users = data["waiting_users"]
            tasks = data["tasks"]
    except FileNotFoundError:
        print("Backup file not found. Starting with empty data.")

# Call the function to load data at the beginning of your script
load_data()

# Your main script logic here

# Call the function to save data when required
save_data()


def main_menu(is_premium_user):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(telebot.types.KeyboardButton("💬 Enter Chat"), 
                 telebot.types.KeyboardButton("❌ Leave Chat"), 
                 telebot.types.KeyboardButton("👥 MY PROFILE"))
    keyboard.add(telebot.types.KeyboardButton("🎰 PLAY LOTTERY"), 
                 telebot.types.KeyboardButton("🌟 MY COINS"))
    keyboard.add(telebot.types.KeyboardButton("⚙️ Settings"), 
                 telebot.types.KeyboardButton("🔄 New Chat"))
    keyboard.add(telebot.types.KeyboardButton("TASK"), 
                 telebot.types.KeyboardButton("/🏆Leaderboard"))


    if is_premium_user:
        keyboard.add(telebot.types.KeyboardButton("SEND VOICE MESSAGE"), 
                     telebot.types.KeyboardButton("SEND STICKERS"))

    # Add the last button in a new row
    keyboard.add(telebot.types.KeyboardButton("REFER FRIENDS"))
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id  

    if user_id not in users:
        users.add(user_id)

    if user_id not in users_db:
        users_db[user_id] = {
            "coins": 0,
            "name": None,
            "username": message.from_user.username,
            "profile_photo": None,
            "status": "idle",
        }
        bot.send_message(
            user_id,
            "👋 Welcome to Real-Time Chatting Bot!\n"
            "📜 Please follow the rules and create your profile to start chatting.",
            reply_markup=create_profile_menu()
        )
    else:
        is_premium_user = user_id in premium_users  # Corrected line
        bot.send_message(
            user_id,
            "👋 Welcome back! Use the menu below to start chatting or manage your profile.",
            reply_markup=main_menu(is_premium_user)  # Pass the correct boolean
        )
        
def create_profile_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📄 Create Profile", callback_data="create_profile"))
    markup.add(types.InlineKeyboardButton("🛠 Support", url="https://t.me/FATHER_OF_HAX"))  # Yahan apni URL daalein
    return markup



@bot.callback_query_handler(func=lambda call: call.data == "create_profile")
def create_profile(call):
    bot.send_message(call.message.chat.id, "📛 Please send your name to create your profile:")
    bot.register_next_step_handler(call.message, get_name)

def get_name(message):
    user_id = message.from_user.id
    users_db[user_id]["name"] = message.text
    bot.send_message(user_id, "📸 Great! Now send your profile photo:")
    bot.register_next_step_handler(message, get_photo)

def get_photo(message):
    user_id = message.from_user.id
    if message.photo:
        photo_file_id = message.photo[-1].file_id
        users_db[user_id]["profile_photo"] = photo_file_id
        
        # User ko 200 coins dein
        user_coins[user_id] = user_coins.get(user_id, 0) + 200
        
        is_premium_user = users_db[user_id].get("is_premium", False)
        bot.send_message(user_id, "✅ Profile created successfully! You've received 200 coins! Use /start to begin chatting.", reply_markup=main_menu(is_premium_user))
    else:
        bot.send_message(user_id, "❌ Please send a valid photo to complete your profile.")

@bot.message_handler(commands=["users"])
def list_users(message):
    # Check if the user is an admin
    if message.from_user.id not in admins:
        bot.send_message(message.chat.id, "Sirf admins is command ko run kar sakte hain.")
        return
        
    if not users:
        bot.send_message(message.chat.id, "Koi user nahi hai.")
    else:
        user_list = []
        for index, user_id in enumerate(users, start=1):
            username = users_db[user_id]['username']
            user_list.append(f"{index}. Username @{username}\nUser id: {user_id}\n")
        
        bot.send_message(message.chat.id, "Users:\n" + "\n".join(user_list))

# Referral tracking
referral_data = {}  # {user_id: {'referred_users': [user_ids], 'total_coins': int}}

@bot.message_handler(func=lambda message: message.text == "REFER FRIENDS")
def refer_friends(message):
    user_id = message.from_user.id

    # Generate a unique referral link
    referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"

    # Initialize referral data for the user if not already present
    if user_id not in referral_data:
        referral_data[user_id] = {'referred_users': [], 'total_coins': 0}

    # Send the referral link to the user
    bot.reply_to(
        message,
        f"Invite your friends using this link:\n\n{referral_link}\n\n"
        "When someone joins using your link, you will earn 50 coins!"
    )
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    user_id = message.from_user.id

    # Check if the user is new
    if user_id not in users:
        users.add(user_id)
        user_coins[user_id] = user_coins.get(user_id, 0)  # Initialize coins for new users

        # Handle referral if a referrer ID is present
        if len(args) > 1:
            try:
                referrer_id = int(args[1])

                # Ensure the referrer is a valid user and not the same as the new user
                if referrer_id in users and referrer_id != user_id:
                    # Add the new user to the referrer's referred users
                    if referrer_id not in referral_data:
                        referral_data[referrer_id] = {'referred_users': [], 'total_coins': 0}
                    if user_id not in referral_data[referrer_id]['referred_users']:
                        referral_data[referrer_id]['referred_users'].append(user_id)

                        # Reward the referrer with 50 coins
                        user_coins[referrer_id] += 50
                        referral_data[referrer_id]['total_coins'] += 50

                        # Notify the referrer
                        bot.send_message(
                            referrer_id,
                            f"🎉 You referred a new user!\n\n"
                            f"User Count: {len(referral_data[referrer_id]['referred_users'])}\n"
                            f"Total Coins Earned: {referral_data[referrer_id]['total_coins']} coins\n\n"
                            f"✅ You earned 50 coins!"
                        )
            except ValueError:
                pass  # Ignore invalid referrer IDs

    # Welcome message for the new user
    is_premium_user = is_premium(user_id)
    bot.send_message(
        user_id,
        "Welcome to the Chat Bot! Choose an option below to get started:",
        reply_markup=main_keyboard(is_premium_user)
    )

@bot.message_handler(commands=["sendc"])
def send_coins_to_user(message):
    if message.from_user.id not in admins:
        bot.reply_to(message, "You are not authorized to use this command.")
        return
    try:
        _, user_id, coins = message.text.split()
        user_id = int(user_id)
        coins = int(coins)
        user_coins[user_id] = user_coins.get(user_id, 0) + coins
        bot.reply_to(message, f"Successfully sent {coins} coins to user {user_id}.")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=["send_coins"])
def send_coins(message):
    try:
        _, user_id, coins = message.text.split()
        user_id = int(user_id)
        coins = int(coins)
        sender_id = message.from_user.id
        if user_coins.get(sender_id, 0) < coins:
            bot.reply_to(message, "You don't have enough coins to send.")
            return
        user_coins[sender_id] -= coins
        user_coins[user_id] = user_coins.get(user_id, 0) + coins
        bot.send_message(user_id, f"You have received {coins} coins from {message.from_user.first_name}!")
        bot.reply_to(message, f"Successfully sent {coins} coins to user {user_id}.")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

def update_leaderboard():
    return sorted(user_coins.items(), key=lambda x: x[1], reverse=True)[:3]

@bot.message_handler(commands=['🏆 Leaderboard'])
def leaderboard_command(message):
    leaderboard = update_leaderboard()
    text = "🏆 Leaderboard:\n"
    
    for i, (user_id, coins) in enumerate(leaderboard, start=1):
        username = users_db[user_id].get("username", "unknown_user")
        premium = "Yes" if user_id in premium_users else "No"
        profile_link = f"https://t.me/{username}"  # Adjust if needed
        text += f"{i}. @{username}\n{coins} Coins\nPremium: {premium}\nProfile: [LINK]({profile_link})\n\n"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['🏆Leaderboard'])
def reload_leaderboard(message):
    user_id = message.from_user.id
    if user_id in admins:
        leaderboard = update_leaderboard()
        text = "🏆 Leaderboard 🆕\n\n" + "🏆 Current Leaderboard:\n"
        
        for i, (user_id, coins) in enumerate(leaderboard, start=1):
            if user_id in users_db: 
                username = users_db[user_id].get("username", "unknown_user")
                premium = "Yes" if user_id in premium_users else "No"
                profile_link = f"https://t.me/{username}" 
                text += f"{i}. @{username}\n{coins} Coins\nPremium: {premium}\nProfile: [LINK]({profile_link})\n\n"
            else:
                text += f"{i}. User ID {user_id} not found in database.\n{coins} Coins\nPremium: No\n\n"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')
    else:
        leaderboard = update_leaderboard()
        text = "🏆 Current Leaderboard:\n"
        
        for i, (user_id, coins) in enumerate(leaderboard, start=1):
            if user_id in users_db: 
                username = users_db[user_id].get("username", "unknown_user")
                premium = "Yes" if user_id in premium_users else "No"
                profile_link = f"https://t.me/{username}" 
                text += f"{i}. @{username}\n{coins} Coins\nPremium: {premium}\nProfile: [LINK]({profile_link})\n\n"
            else:
                text += f"{i}. User ID {user_id} not found in database.\n{coins} Coins\nPremium: No\n\n"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "TASK")
def give_task(message):
    user_id = message.from_user.id
    if tasks:
        task = tasks[0]
        task_text = f"Task: {task['description']}"
        bot.send_message(message.chat.id, task_text)
        users_db[user_id]['current_task'] = task
        markup = types.InlineKeyboardMarkup()
        complete_button = types.InlineKeyboardButton("Mark as Completed", callback_data='complete_task')
        markup.add(complete_button)
        bot.send_message(message.chat.id, "Complete the task and press the button below!", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "No tasks available at the moment.")

@bot.callback_query_handler(func=lambda call: call.data == 'complete_task')
def complete_task(call):
    user_id = call.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {'coins': 0}
    if 'coins' not in users_db[user_id]:
        users_db[user_id]['coins'] = 0
    if 'current_task' in users_db[user_id]:
        task = users_db[user_id]['current_task']
        if 'reward' in task:
            users_db[user_id]['coins'] += task['reward']
            bot.send_message(call.message.chat.id, f"Task completed! You earned {task['reward']} coins. Total coins: {users_db[user_id]['coins']}")
            del users_db[user_id]['current_task']
        else:
            bot.send_message(call.message.chat.id, "This task has no reward.")
    else:
        bot.send_message(call.message.chat.id, "You have no active tasks.")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
Yeh hai aapke liye madad sandeś:

/send_coins - SEND COINS TO OTHER USERS
/buy - TO BUY COINS OR MEMBERSHIP

MORE COMMANDS COMMING 

STAY TUNED 📈
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['broadcast'])
def broadcast_start(message):
    user_id = message.from_user.id
    if user_id in admins:
        bot.send_message(user_id, "📢 Please provide your message, photo, or video:")
        bot.register_next_step_handler(message, process_broadcast_message)
    else:
        bot.send_message(user_id, "❌ You do not have permission to perform this action.")

def process_broadcast_message(message):
    user_id = message.from_user.id
    
    if message.content_type == 'text':
        text_message = message.text
        for subscriber in users:
            bot.send_message(subscriber, f"📢 New Broadcast: {text_message}")

    elif message.content_type == 'photo':
        photo_file_id = message.photo[-1].file_id 
        caption = message.caption if message.caption else "No caption provided."

        for subscriber in users:
            bot.send_photo(subscriber, photo_file_id, caption=caption)

    elif message.content_type == 'video':
        video_file_id = message.video.file_id
        caption = message.caption if message.caption else "No caption provided."
        for subscriber in users:
            bot.send_video(subscriber, video_file_id, caption=caption)

    else:
        bot.send_message(user_id, "❌ Unsupported media type. Please send text, photo, or video.")

    bot.send_message(user_id, "✅ Your message has been broadcasted!")

@bot.message_handler(commands=['add_task'])
def add_task(message):
    try:
        task_details = message.text[len('/add_task '):].strip().rsplit(' ', 1)
        if len(task_details) != 2:
            raise ValueError
        
        task_description = task_details[0]
        reward = int(task_details[1])
        tasks.append({"description": task_description, "reward": reward})
        bot.send_message(message.chat.id, f"Task added: {task_description} (Reward: {reward} coins)")
    except ValueError:
        bot.send_message(message.chat.id, "Please use the format: /add_task <task_description> <reward>")

@bot.message_handler(commands=['set'])
def set_leaderboard_member(message):
    user_id = message.from_user.id

    if user_id not in admins:
        bot.send_message(message.chat.id, "❌ You are not authorized to set leaderboard members.")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.send_message(message.chat.id, "Usage: /set <user_name or user_id> <coins>")
        return

    user_input = args[1]
    coins = int(args[2])
    if user_input.isdigit():
        target_id = int(user_input)
    else:
        target_id = next((uid for uid, profile in users_db.items() if profile.get("username") == user_input), None)

    if target_id is not None and target_id in users_db:
        user_coins[target_id] = coins
        bot.send_message(message.chat.id, f"✅ {user_input}'s coins set to {coins}.")
    else:
        bot.send_message(message.chat.id, "❌ User not found.")

@bot.message_handler(commands=["sendm"])
def grant_premium(message):
    if message.from_user.id not in admins:
        bot.reply_to(message, "You are not authorized to use this command.")
        return
    try:
        _, user_id, duration = message.text.split()
        user_id = int(user_id)
        time_unit = duration[-3:]  # e.g., 'day', 'yr'
        time_value = int(duration[:-3])  # e.g., '1', '2'

        if time_unit == "day":
            expiry = datetime.now() + timedelta(days=time_value)
        elif time_unit == "yr":
            expiry = datetime.now() + timedelta(days=365 * time_value)
        else:
            bot.reply_to(message, "Invalid duration format. Use '1day', '2day', or '1yr'.")
            return

        premium_users[user_id] = expiry
        bot.reply_to(message, f"Granted premium membership to user {user_id} until {expiry}.")
        bot.send_message(user_id, "🎉 You have been granted premium membership! Enjoy the exclusive features.")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=["remove_m"])
def remove_premium(message):
    if message.from_user.id not in admins:
        bot.reply_to(message, "You are not authorized to use this command.")
        return
    try:
        _, user_id = message.text.split()
        user_id = int(user_id)
        if user_id in premium_users:
            del premium_users[user_id]
            bot.reply_to(message, f"Removed premium membership from user {user_id}.")
            bot.send_message(user_id, "Your premium membership has been revoked.")
        else:
            bot.reply_to(message, f"User {user_id} does not have premium membership.")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")


@bot.message_handler(func=lambda message: message.text == "SEND VOICE MESSAGE")
def send_voice_message(message):
    if is_premium(message.from_user.id):
        bot.reply_to(message, "You can now send voice messages!")
    else:
        bot.reply_to(message, "This feature is available for premium users only.")

@bot.message_handler(func=lambda message: message.text == "SEND STICKERS")
def send_stickers(message):
    if is_premium(message.from_user.id):
        bot.reply_to(message, "You can now send stickers!")
    else:
        bot.reply_to(message, "This feature is available for premium users only.")

import random
import time



@bot.message_handler(func=lambda message: message.text == "🎰 PLAY LOTTERY")
def play_lottery(message):
    user_id = message.from_user.id
    if user_coins.get(user_id, 0) < 10:
        bot.reply_to(message, "❌ Aapko lottery khelne ke liye kam se kam 10 coins ki zaroorat hai! Apne coins badhao aur phir se try karo! 💪")
        return

    # 5 random hint numbers generate karna
    hint_numbers = random.sample(range(1000, 5001), 5)
    hint_message = f"🎲 Ek number chune (1000-5000) aur bet amount chune (jaise '1200 50').\n🎯 Hint: {', '.join(map(str, hint_numbers))} (soch samajh kar chune! 🤔)"
    
    bot.reply_to(message, hint_message)
    bot.register_next_step_handler(message, process_lottery)

def process_lottery(message):
    try:
        user_id = message.from_user.id
        number, bet = map(int, message.text.split())
        if number < 1000 or number > 5000 or bet < 10:
            raise ValueError("🚫 Invalid number ya bet! Sahi range mein chuno!")

        user_coins[user_id] -= bet
        
        response_message = bot.reply_to(message, "🔄 Aapka bet process ho raha hai... Please wait! ⏳")

        # Jab tak output dikhana hai
        for i in range(40):
            display_message = ""
            for j in range(20):  # 15 lines
                line_numbers = [str(random.randint(1000, 5000)) for _ in range(7)]  # 3 numbers in each line
                display_message += " ".join(line_numbers) + "\n"

            bot.edit_message_text(chat_id=response_message.chat.id, message_id=response_message.message_id, 
                                  text=display_message.strip())
            time.sleep(0.1)

        # List of winning numbers
        winning_numbers = random.sample(range(1000, 5001), 700)
        
        # Results display karna
        result_message = "🎉 Results aa gaye! 🎉\n\n✨ Winning numbers the: " + " ".join(map(str, winning_numbers)) + "\n\n🔔 Kya aapka number hai? 🔔"
        bot.edit_message_text(chat_id=response_message.chat.id, message_id=response_message.message_id, 
                              text=result_message)

        if number in winning_numbers:
            winnings = bet * 2
            user_coins[user_id] += winnings
            bot.reply_to(message, f"🎈 Congratulations! 🎈 Aapne {winnings} coins jeete! 🎊 Aapka lucky number chuna gaya! 🎉")
        else:
            bot.reply_to(message, "😢 Oh no! Aapka number nahi aaya. Behtar luck agle baar! 🍀")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e} \nKuch galat hua! Koshish dobarah karein. 🔄")

@bot.message_handler(func=lambda message: message.text == "👥 MY PROFILE")
def my_profile(message):
    user_id = message.from_user.id
    premium_status = "Yes" if is_premium(user_id) else "No"
    coins = user_coins.get(user_id, 0)
    
    profile = users_db.get(user_id, None)
    
    if profile:
        name = profile.get("name", "Unnamed") 
        username = profile.get("username", "Not set")
        bot.send_photo(
            user_id,
            profile.get("profile_photo", None),
            caption=f"👤 Your Profile:\n\n"
                    f"📛 Name: {name}\n"
                    f"🔗 Username: @{username}\n"
                    f"🆔 ID: {user_id}\n"
                    f"- Premium: {premium_status}\n"
                    f"Coins: {coins}\n"
        )
    else:
        bot.send_message(user_id, "❌ Profile not found. Use '📄 Create Profile' to create one.")

@bot.message_handler(func=lambda message: message.text == "⚙️ Settings")
def settings(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "⚙️ Settings:\n\n1. Change Name\n2. Change Profile Photo\n\nPlease type your choice (e.g., '1' for Change Name):")
    bot.register_next_step_handler(message, handle_settings)
def handle_settings(message):
    user_id = message.from_user.id
    choice = message.text.strip()
    if choice == "1":
        bot.send_message(user_id, "📛 Send your new name:")
        bot.register_next_step_handler(message, update_name)
    elif choice == "2":
        bot.send_message(user_id, "📸 Send your new profile photo:")
        bot.register_next_step_handler(message, update_photo)
    else:
        bot.send_message(user_id, "❌ Invalid choice. Use '⚙️ Settings' again.")

def update_name(message):
    user_id = message.from_user.id
    users_db[user_id]["name"] = message.text
    bot.send_message(user_id, "✅ Name updated successfully!")

def update_photo(message):
    user_id = message.from_user.id
    if message.photo:
        photo_file_id = message.photo[-1].file_id
        users_db[user_id]["profile_photo"] = photo_file_id
        bot.send_message(user_id, "✅ Profile photo updated successfully!")
    else:
        bot.send_message(user_id, "❌ Please send a valid photo.")



@bot.message_handler(commands=['buy'])
def send_coins_details(message):
    coins_details = (
        "🪙 **COINS DETAILS:**\n"
        "💰 **100 COINS** - ₹ 30 🎉\n"
        "💰 **200 COINS** - ₹ 50 💵\n"
        "💰 **300 COINS** - ₹ 75 🤑\n"
        "💰 **500 COINS** - ₹ 120 🏆\n"
        "💰 **1000 COINS** - ₹ 200 🎁\n"
        "💰 **2000 COINS** - ₹ 400 💳\n"
        "💰 **5000 COINS** - ₹ 1000 🏅\n"
        "💰 **10000 COINS** - ₹ 2000 🌟\n"
        "💰 **15000 COINS** - ₹ 3000 👑\n"
        "💰 **20000 COINS** - ₹ 4000 🚀\n"
        "💰 **30000 COINS** - ₹ 6000 🌈\n"
        "💰 **50000 COINS** - ₹ 10000 🎊\n"
        "\n"
        "🌟 **MEMBERSHIP** 🌟\n"
        "💎 **PRICE** - ₹ 200 🎉\n"
        "✨ Enjoy exclusive benefits and perks! ✨\n"
    )
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    buy_button = telebot.types.InlineKeyboardButton("🛒 BUY NOW", url="https://t.me/FATHER_OF_HAX")
    keyboard.add(buy_button)

    bot.send_message(message.chat.id, coins_details, reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "🌟 MY COINS")
def send_my_coins(message):
    user_id = message.from_user.id
    premium_status = "Yes" if is_premium(user_id) else "No"
    coins = user_coins.get(user_id, 0)

    my_coins_details = (
        "🌟 **MY COINS** 🌟\n"
        f"- **Premium:** {premium_status}\n"
        f"- **Coins:** {coins}\n"
    )

    keyboard = telebot.types.InlineKeyboardMarkup()
    refresh_button = telebot.types.InlineKeyboardButton("🔄 REFRESH", callback_data='refresh_coins')
    keyboard.add(refresh_button)

    bot.send_message(message.chat.id, my_coins_details, reply_markup=keyboard)


from datetime import datetime

def is_premium(user_id):
    if user_id in premium_users:
        return datetime.now() < premium_users[user_id]
    return False

def send_entry_message_to_chat(new_user_id, chat_partner_id):
    try:
        bot.send_message(new_user_id, "Aap chat mein enter ho gaye hain.")
        bot.send_message(chat_partner_id, "Aapka naya user connect ho gaya hai, chatting shuru karein.")
        if is_premium(new_user_id):
            user_info = bot.get_chat(new_user_id)
            photo = bot.get_user_profile_photos(new_user_id)

            if photo.total_count > 0:
                file_id = photo.photos[0][0].file_id
                bot.send_photo(
                    chat_partner_id,
                    file_id,
                    caption=f"🎉 VIP user {user_info.first_name} entered your chat!"
                )
            else:
                bot.send_message(
                    chat_partner_id,
                    f"🎉 VIP user {user_info.first_name} entered your chat!"
                )
    except Exception as e:
        bot.send_message(new_user_id, f"Error: {e}")
        bot.send_message(chat_partner_id, f"Error: {e}")

@bot.message_handler(func=lambda message: message.text == "💬 Enter Chat")
def enter_chat(message):
    user_id = message.from_user.id
    if user_id in active_chats:
        bot.send_message(user_id, "❌ You are already in a chat. Use '🔄 New Chat' to find a new partner.")
        return

    bot.send_message(user_id, "🔍 Searching for a user to chat with...")
    if waiting_users and waiting_users[0] != user_id:
        partner_id = waiting_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        # Notify both users
        partner_profile = users_db[partner_id]
        user_profile = users_db[user_id]

        bot.send_photo(user_id, partner_profile["profile_photo"], caption=f"📩 User found! You are now chatting with {partner_profile['name']} (@{partner_profile['username']}).")
        bot.send_photo(partner_id, user_profile["profile_photo"], caption=f"📩 User found! You are now chatting with {user_profile['name']} (@{user_profile['username']}).")
    else:
        waiting_users.append(user_id)
        bot.send_message(user_id, "⏳ Waiting for another user to join...")


@bot.message_handler(func=lambda message: message.text == "❌ Leave Chat")
def leave_chat(message):
    user_id = message.from_user.id
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)

        bot.send_message(partner_id, "❌ Your partner has left the chat.")
        bot.send_message(user_id, "✅ You have left the chat.")
    else:
        bot.send_message(user_id, "❌ You are not in a chat.")


# New message handler to forward messages between connected users
@bot.message_handler(func=lambda message: True)
def forward_message(message):
    user_id = message.from_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        bot.send_message(partner_id, f"{message.text}")

@bot.message_handler(func=lambda message: message.text == "🔄 New Chat")
def new_chat(message):
    leave_chat(message)
    enter_chat(message)


bot.infinity_polling()