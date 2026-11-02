import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
from flask import Flask
from threading import Thread

# ඔබේ Token එක මෙතනට දාන්න
TOKEN = "9089642039:AAHjKIb-1wU5QJp_XGABSEOEvC5PsjIvRcE"
bot = telebot.TeleBot(TOKEN)

# ලින්ක් මතක තබා ගැනීමට
user_links = {}

# Image එකත් සමඟ යන Professional Welcome Message එක
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_msg = (
        "Welcome to Social Media Video Downloader! 🚀\n\n"
        "Send me a link from one of these sites:\n\n"
        "▶️ YouTube · 🎵 TikTok · 📸 Instagram\n"
        "📌 Pinterest · 𝕏 Twitter · 👤 Facebook\n\n"
        "Then choose:\n"
        "🎦 Video (MP4) · 🎶 Audio (MP3)\n\n"
        "⚠️ Send /help for details"
    )
    
    try:
        # පින්තූරය සමඟ මැසේජ් එක යැවීම
        with open('Gemini_Generated_Image_mezbhmmezbhmmezb.jfif', 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=welcome_msg)
    except FileNotFoundError:
        # පින්තූරය නැති වුණොත් සාමාන්‍ය විදිහට මැසේජ් එක යැවීම
        bot.send_message(chat_id, welcome_msg)

# Help Command Message එක (/help)
@bot.message_handler(commands=['help'])
def send_help(message):
    help_msg = (
        "🛠️ **Bot Help & Information**\n\n"
        "1️⃣ Send any video link from supported platforms (YouTube, TikTok, Facebook, etc.).\n"
        "2️⃣ Choose your preferred quality (144p to 4K) or select 320kbps MP3 Audio.\n"
        "3️⃣ Wait a few seconds while the bot processes and sends your file.\n\n"
        "⚠️ **Important Note:** Telegram has a 50MB file size limit for bots. If you select 4K or 1080p, it will only work for short videos (like Shorts or Reels)."
    )
    bot.reply_to(message, help_msg, parse_mode='Markdown')

# ලින්ක් එකක් එව්වම බොත්තම් පෙන්වීම
@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = message.text
    chat_id = message.chat.id
    
    user_links[chat_id] = url
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    
    markup.add(
        InlineKeyboardButton("144p", callback_data="144"),
        InlineKeyboardButton("240p", callback_data="240"),
        InlineKeyboardButton("360p", callback_data="360"),
        InlineKeyboardButton("480p", callback_data="480"),
        InlineKeyboardButton("720p", callback_data="720"),
        InlineKeyboardButton("1080p", callback_data="1080")
    )
    markup.add(
        InlineKeyboardButton("1440p (2K)", callback_data="1440"),
        InlineKeyboardButton("2160p (4K)", callback_data="2160")
    )
    markup.add(InlineKeyboardButton("🎶 Audio Only (320kbps MP3)", callback_data="mp3"))
    
    bot.reply_to(message, "👇 Please choose the format:", reply_markup=markup)

# බොත්තමක් Click කළ විට ක්‍රියාත්මක වන කොටස
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    data = call.data 
    
    if chat_id not in user_links:
        bot.answer_callback_query(call.id, "Link expired. Please send the link again.")
        return

    url = user_links[chat_id]
    
    if data == "mp3":
        bot.edit_message_text("⏳ Processing 320kbps MP3 Audio, please wait...", chat_id=chat_id, message_id=call.message.message_id)
        ydl_opts = {
            'outtmpl': f'audio_{chat_id}.%(ext)s',
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        }
        file_name = f'audio_{chat_id}.mp3'
        
    else:
        bot.edit_message_text(f"⏳ Downloading {data}p video, please wait...", chat_id=chat_id, message_id=call.message.message_id)
        ydl_opts = {
            'outtmpl': f'video_{chat_id}.mp4',
            'format': f'bestvideo[height<={data}][ext=mp4]+bestaudio[ext=m4a]/best[height<={data}][filesize<50M]/best[filesize<50M]',
            'merge_output_format': 'mp4',
        }
        file_name = f'video_{chat_id}.mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file_size = os.path.getsize(file_name)
        
        if file_size > 52428800:
            bot.send_message(chat_id, "❌ Sorry, the file is larger than 50MB. Please choose a lower quality.")
        else:
            with open(file_name, 'rb') as file:
                if data == "mp3":
                    bot.send_audio(chat_id, file, caption="✅ 320kbps MP3 Audio")
                else:
                    q_text = "4K" if data == "2160" else "2K" if data == "1440" else f"{data}p"
                    bot.send_video(chat_id, file, caption=f"✅ {q_text} Quality Video")

        os.remove(file_name)
        bot.delete_message(chat_id, call.message.message_id)

    except Exception as e:
        bot.send_message(chat_id, "❌ Error! Make sure FFmpeg is installed or the video is public.")
        try:
            os.remove(file_name)
        except:
            pass

# ==========================================
# Render සර්වර් එක සඳහා Dummy Web Server එක
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running 24/7 on Render!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

print("බොට් වැඩ කරනවා... (Render Server Mode)")
keep_alive()
bot.polling(non_stop=True)