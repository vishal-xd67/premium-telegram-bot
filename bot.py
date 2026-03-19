import io
import zipfile
import os
import json
import time
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

TOKEN = "8645594144:AAGSp_PyyvK_OAKhtp67lbFy2RW1-NRDjwk"
ADMIN_ID = 7951917601
CHANNEL_USERNAME = "@Primexgen"
FREE_COOLDOWN = 7200
PREMIUM_COOLDOWN = 3600
PREMIUM_TIME = 432000
PREMIUM_ACCOUNT_COOLDOWN = 86400

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot Running ✅"


def run_flask():
    app.run(host="0.0.0.0", port=8080, debug=False)


def keep_alive():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()


def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default


def save_data(file, data):
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {file}: {e}")


users = {}
invites = {}
premium = {}
cooldowns = {}
netflix_stock = []
chatgpt_stock = []
spotify_stock = []
netflix_accounts = []
waiting_zip = {}


def save_all():
    save_data("users.json", users)
    save_data("invites.json", invites)
    save_data("premium.json", premium)
    save_data("cooldowns.json", cooldowns)
    save_data("netflix_stock.json", netflix_stock)
    save_data("chatgpt_stock.json", chatgpt_stock)
    save_data("spotify_stock.json", spotify_stock)
    save_data("netflix_accounts.json", netflix_accounts)


users = load_data("users.json", {})
invites = load_data("invites.json", {})
premium = load_data("premium.json", {})
# ensure keys are strings so add/remove/list always match
premium = {str(k): v for k, v in premium.items()}
cooldowns = load_data("cooldowns.json", {})
netflix_stock = load_data("netflix_stock.json", [])
chatgpt_stock = load_data("chatgpt_stock.json", [])
spotify_stock = load_data("spotify_stock.json", [])
netflix_accounts = load_data("netflix_accounts.json", [])


def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def is_channel_member(bot, user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


def is_premium_user(user_id, now):
    user_id = str(user_id)
    return user_id in premium and premium[user_id] > now


def get_cooldown(user_id, now):
    if is_premium_user(user_id, now):
        return PREMIUM_COOLDOWN
    return FREE_COOLDOWN


def check_cooldown(query, user_id, now):
    if str(user_id) == str(ADMIN_ID):
        return False

    if user_id in cooldowns and cooldowns[user_id] > now:
        remaining = cooldowns[user_id] - now
        query.message.reply_text(
            f"⏳ Cooldown Active!\n\nWait {format_time(remaining)}"
        )
        return True
    return False


def main_menu():
    keyboard = [
        [InlineKeyboardButton("💳 Free Services", callback_data="free")],
        [InlineKeyboardButton("💎 Premium Services", callback_data="premium")],
        [InlineKeyboardButton("👥 Invite Friends", callback_data="invite")],
        [InlineKeyboardButton("🎁 Daily Bonus", callback_data="bonus")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leader")],
        [InlineKeyboardButton("📞 Support", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)


WELCOME_TEXT = "👋 Welcome to Premium Cookies Bot\n\n💎 Invite 3 friends to unlock Premium\n\n👇 Choose an option below"


def start(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)

    if not is_channel_member(context.bot, int(user_id)):
        kb = [
            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}",
                )
            ],
            [InlineKeyboardButton("✅ Verify", callback_data="verify")],
        ]
        update.message.reply_text(
            "⚠️ Please join our channel first", reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    if user_id not in users:
        users[user_id] = True
        invites[user_id] = invites.get(user_id, 0)

        if context.args:
            ref_id = str(context.args[0])

            # self invite block
            if ref_id != user_id:
                key = f"{user_id}_{ref_id}"

                # duplicate invite block
                if key not in users:
                    users[key] = True

                    invites[ref_id] = invites.get(ref_id, 0) + 1

                    if invites[ref_id] >= 3:
                        premium[ref_id] = int(time.time()) + PREMIUM_TIME

        save_all()

    update.message.reply_text(WELCOME_TEXT, reply_markup=main_menu())


def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = str(query.from_user.id)
    now = int(time.time())
    invite_count = invites.get(user_id, 0)

    if invite_count >= 3 and user_id not in premium:
        premium[user_id] = now + PREMIUM_TIME
        save_all()

    if not is_channel_member(context.bot, int(user_id)):
        query.answer("⚠️ Join channel first", show_alert=True)
        return

    data = query.data

    if data == "verify":
        if is_channel_member(context.bot, int(user_id)):
            query.edit_message_text(WELCOME_TEXT, reply_markup=main_menu())
        else:
            query.answer("❌ You haven't joined the channel", show_alert=True)

    elif data == "free":
        kb = [
            [InlineKeyboardButton("🍪 Netflix Cookie", callback_data="netflix")],
            [InlineKeyboardButton("🤖 ChatGPT Cookie", callback_data="chatgpt")],
            [InlineKeyboardButton("🎵 Spotify Cookie", callback_data="spotify")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")],
        ]
        query.edit_message_text(
            f"💳 Free Services\n\n📺 Netflix Stock: {len(netflix_stock)}\n🤖 ChatGPT Stock: {len(chatgpt_stock)}\n🎵 Spotify Stock: {len(spotify_stock)}",
            reply_markup=InlineKeyboardMarkup(kb),
        )

    elif data == "netflix":
        if check_cooldown(query, user_id, now):
            return

        if netflix_stock:
            cookie = netflix_stock.pop(0)
        elif int(user_id) == ADMIN_ID:
            cookie = "ADMIN_TEST_COOKIE"
        else:
            query.answer("❌ Netflix Cookies Out Of Stock", show_alert=True)
            return

        file = io.BytesIO(cookie.encode("utf-8"))
        file.seek(0)
        file.name = "cookie.txt"

        context.bot.send_document(
            chat_id=query.message.chat.id, document=file, caption="🍪 Netflix Cookie"
        )

        cooldowns[user_id] = now + get_cooldown(user_id, now)
        save_all()

        context.bot.send_message(
            query.message.chat.id, "✅ Netflix Cookie Sent Successfully"
        )

    elif data == "chatgpt":
        if check_cooldown(query, user_id, now):
            return

        if not chatgpt_stock and int(user_id) != ADMIN_ID:
            query.answer("❌ ChatGPT Cookies Out Of Stock", show_alert=True)
            return

        if chatgpt_stock:
            cookie = chatgpt_stock.pop(0)
        else:
            cookie = "ADMIN_TEST_COOKIE"

        file = io.BytesIO(cookie.encode("utf-8"))
        file.seek(0)
        file.name = "cookie.txt"

        context.bot.send_document(
            chat_id=query.message.chat.id, document=file, caption="🤖 ChatGPT Cookie"
        )

        cooldowns[user_id] = now + get_cooldown(user_id, now)
        save_all()

        query.message.reply_text("✅ ChatGPT Cookie Sent Successfully")

    elif data == "spotify":
        if check_cooldown(query, user_id, now):
            return

        if not spotify_stock and int(user_id) != ADMIN_ID:
            query.answer("❌ Spotify Cookies Out Of Stock", show_alert=True)
            return

        if spotify_stock:
            cookie = spotify_stock.pop(0)
        else:
            cookie = "ADMIN_TEST_COOKIE"

        file = io.BytesIO(cookie.encode("utf-8"))
        file.seek(0)
        file.name = "cookie.txt"

        context.bot.send_document(
            chat_id=query.message.chat.id, document=file, caption="🎵 Spotify Cookie"
        )

        cooldowns[user_id] = now + get_cooldown(user_id, now)
        save_all()

        query.message.reply_text("✅ Spotify Cookie Sent Successfully")

    elif data == "premium":
        # ⭐ ADMIN BYPASS
        if str(user_id) == str(ADMIN_ID):
            kb = [
                [
                    InlineKeyboardButton(
                        "📺 Get Netflix Account", callback_data="netflixacc"
                    )
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="back")],
            ]
            query.edit_message_text(
                f"👑 ADMIN PANEL\n\n📺 Netflix Accounts: {len(netflix_accounts)}",
                reply_markup=InlineKeyboardMarkup(kb),
            )
            return

        # ⭐ PREMIUM CHECK
        if is_premium_user(user_id, now):
            kb = [
                [
                    InlineKeyboardButton(
                        "📺 Get Netflix Account", callback_data="netflixacc"
                    )
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="back")],
            ]

            query.edit_message_text(
                f"💎 Premium Active\n\n📺 Netflix Accounts: {len(netflix_accounts)}",
                reply_markup=InlineKeyboardMarkup(kb),
            )

        else:
            invite_count = invites.get(user_id, 0)
            need = 3 - invite_count
            progress = "🟢" * invite_count + "⚪" * need

            kb = [
                [InlineKeyboardButton("👥 Invite Friends", callback_data="invite")],
                [
                    InlineKeyboardButton(
                        "💰 Buy Premium Instant", callback_data="buypremium"
                    )
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="back")],
            ]

            query.edit_message_text(
                f"🔒 Premium Locked\n\n📊 Progress: {progress} ({invite_count}/3)\nInvite {need} more friends",
                reply_markup=InlineKeyboardMarkup(kb),
            )
    elif data == "buypremium":
        text = "💎 Buy Premium Instant\n\n📋 Benefits:\n• Faster Cookie Access\n• 1 Hour Cooldown\n• Priority Stock\n\nContact Admin:\n@Mrf1005"
        kb = [
            [InlineKeyboardButton("📱 Contact Admin", url="https://t.me/Mrf1005")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")],
        ]
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif data == "netflixacc":
        if str(user_id) != str(ADMIN_ID) and not is_premium_user(user_id, now):
            query.answer("❌ Premium Only Service", show_alert=True)
            return

        # ADMIN BYPASS COOLDOWN
        if int(user_id) != ADMIN_ID:
            if check_cooldown(query, user_id, now):
                return

        if not netflix_accounts:
            query.answer("❌ Netflix Accounts Out Of Stock", show_alert=True)
            return

        account = netflix_accounts.pop(0)

        context.bot.send_message(
            chat_id=query.message.chat.id,
            text=f"📺 Netflix Account\n\n{account}",
            parse_mode="Markdown",
        )

        if int(user_id) != ADMIN_ID:
            cooldowns[user_id] = now + PREMIUM_ACCOUNT_COOLDOWN

        save_all()

        query.message.reply_text("✅ Netflix Account Sent Successfully")
    elif data == "bonus":
        query.answer("🎁 Daily Bonus coming soon!", show_alert=True)

    elif data == "invite":
        bot_username = context.bot.username
        invite_link = f"https://t.me/{bot_username}?start={user_id}"
        invite_count = invites.get(user_id, 0)
        text = f"👥 Invite Friends\n\n🔗 Your Invite Link:\n`{invite_link}`\n\n📊 Invites: {invite_count}/3\n\nInvite 3 friends to unlock Premium 💎"
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
        )

    elif data == "leader":
        if not invites:
            text = "🏆 Leaderboard Empty"
        else:
            top_users = sorted(invites.items(), key=lambda x: x[1], reverse=True)[:10]
            text = "🏆 Top Inviters\n\n"
            for i, (uid, count) in enumerate(top_users, start=1):
                text += f"{i}. {uid} - {count} invites\n"
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown"
        )

    elif data == "support":
        text = "📞 Support\n\nContact admin for help:\n@Mrf1005"
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif data == "back":
        query.edit_message_text(WELCOME_TEXT, reply_markup=main_menu())


def admin_panel(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    help_text = """👑 ADMIN PANEL

🍪 /addnetflix
🤖 /addchatgpt
📺 /addnetflixacc
🎵 /addspotify
💎 /addpremium
❌ /removepremium
📋 /premiumlist
📢 /broadcast
📦 /stock
👥 /users
🗑️ /clearstock"""
    update.message.reply_text(help_text)


def broadcast_msg(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not context.args:
        update.message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)
    sent, failed = 0, 0
    for user_id in list(users.keys()):
        try:
            context.bot.send_message(chat_id=int(user_id), text=message)
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1
    update.message.reply_text(
        f"📢 Broadcast Done\n\n✅ Sent: {sent}\n❌ Failed: {failed}"
    )


def check_stock(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    update.message.reply_text(
        f"📦 STOCK STATUS\n\n📺 Netflix Cookies: {len(netflix_stock)}\n🤖 ChatGPT Cookies: {len(chatgpt_stock)}\n🎵 Spotify Cookies: {len(spotify_stock)}\n📺 Netflix Accounts: {len(netflix_accounts)}"
    )


def total_users_cmd(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    update.message.reply_text(f"👥 Total Users: {len(users)}")


def clear_stock(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    netflix_stock.clear()
    chatgpt_stock.clear()
    spotify_stock.clear()
    netflix_accounts.clear()
    save_all()
    update.message.reply_text("🗑️ All Stock Cleared ✅")


def add_premium(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        update.message.reply_text("Usage: /addpremium <user_id>")
        return

    uid = context.args[0].strip()

    premium[uid] = int(time.time()) + PREMIUM_TIME
    save_all()

    update.message.reply_text(f"✅ Premium added for {uid}")


def remove_premium(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        update.message.reply_text("Usage: /removepremium <user_id>")
        return

    uid = context.args[0].strip()

    if uid in premium:
        del premium[uid]
        save_all()
        update.message.reply_text(f"✅ Premium removed for {uid}")
    else:
        update.message.reply_text(f"❌ User {uid} not found")


def premium_list(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not premium:
        update.message.reply_text("📋 No premium users")
        return
    now = int(time.time())
    active = []
    expired = []
    for uid, expiry in premium.items():
        if expiry > now:
            remaining = expiry - now
            active.append(f"{uid} - {format_time(remaining)} left")
        else:
            expired.append(f"{uid} - Expired")
    text = "💎 PREMIUM USERS\n\n"
    if active:
        text += "✅ ACTIVE:\n" + "\n".join(active[:20]) + "\n\n"
    if expired:
        text += "⏰ EXPIRED:\n" + "\n".join(expired[:20])
    text += f"\n📊 Total: {len(premium)} | Active: {len(active)}"
    update.message.reply_text(text, parse_mode="Markdown")


def add_netflix(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    waiting_zip[update.message.from_user.id] = "netflix"
    update.message.reply_text(
        "📦 Send Netflix ZIP file now\n\n📋 ZIP should contain .txt files with cookies\n📄 1 TXT file = 1 cookie"
    )


def add_chatgpt(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    waiting_zip[update.message.from_user.id] = "chatgpt"
    update.message.reply_text(
        "🤖 Send ChatGPT ZIP file now\n\n📋 ZIP should contain .txt files with cookies\n📄 1 TXT file = 1 cookie"
    )


def add_spotify(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    waiting_zip[update.message.from_user.id] = "spotify"
    update.message.reply_text(
        "🎵 Send Spotify ZIP file now\n\n📋 ZIP should contain .txt files with cookies\n📄 1 TXT file = 1 cookie"
    )


def add_netflix_accounts(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return
    waiting_zip[update.message.from_user.id] = "netflixacc"
    update.message.reply_text(
        "📺 Send Netflix Accounts ZIP file now\n\n📋 ZIP should contain .txt files\n📄 Each line = 1 account (email:password)\n📋 Example:\nuser1@gmail.com:pass123"
    )


def handle_zip_file(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID or user_id not in waiting_zip or not update.message.document:
        return

    try:
        file_obj = context.bot.get_file(update.message.document.file_id)
        file_bytes = io.BytesIO()
        file_obj.download(out=file_bytes)
        file_bytes.seek(0)
        service = waiting_zip[user_id]

        service_names = {
            "netflix": "Netflix Cookies",
            "chatgpt": "ChatGPT Cookies",
            "spotify": "Spotify Cookies",
            "netflixacc": "Netflix Accounts",
        }

        if service == "netflix":
            stock_list = netflix_stock
        elif service == "chatgpt":
            stock_list = chatgpt_stock
        elif service == "spotify":
            stock_list = spotify_stock
        elif service == "netflixacc":
            stock_list = netflix_accounts
        else:
            update.message.reply_text("❌ Invalid service")
            del waiting_zip[user_id]
            return

        added = 0
        with zipfile.ZipFile(file_bytes) as zip_file:
            for file_name in zip_file.namelist():
                if not file_name.lower().endswith(".txt"):
                    continue
                with zip_file.open(file_name) as txt_file:
                    content = txt_file.read().decode("utf-8", errors="ignore").strip()
                    if service == "netflixacc":
                        lines = content.splitlines()
                        for line in lines:
                            acc = line.strip()
                            if acc and acc not in stock_list:
                                stock_list.append(acc)
                                added += 1
                    else:
                        cookie = content
                        if cookie and cookie not in stock_list:
                            stock_list.append(cookie)
                            added += 1

        del waiting_zip[user_id]
        save_all()
        update.message.reply_text(
            f"✅ {service_names.get(service, service)} Added!\n📦 Total Added: {added}\n📊 Current Stock: {len(stock_list)}"
        )
    except Exception as e:
        update.message.reply_text(f"❌ Error processing ZIP: {str(e)}")
        if user_id in waiting_zip:
            del waiting_zip[user_id]


def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("❌ Unknown command. Use /start")


def main():
    keep_alive()
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_panel))
    dp.add_handler(CommandHandler("broadcast", broadcast_msg))
    dp.add_handler(CommandHandler("stock", check_stock))
    dp.add_handler(CommandHandler("users", total_users_cmd))
    dp.add_handler(CommandHandler("clearstock", clear_stock))
    dp.add_handler(CommandHandler("addpremium", add_premium))
    dp.add_handler(CommandHandler("removepremium", remove_premium))
    dp.add_handler(CommandHandler("premiumlist", premium_list))
    dp.add_handler(CommandHandler("addnetflix", add_netflix))
    dp.add_handler(CommandHandler("addchatgpt", add_chatgpt))
    dp.add_handler(CommandHandler("addspotify", add_spotify))
    dp.add_handler(CommandHandler("addnetflixacc", add_netflix_accounts))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.document, handle_zip_file))
    dp.add_handler(MessageHandler(Filters.command, unknown))

    print("🤖 Bot Started Successfully!")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
