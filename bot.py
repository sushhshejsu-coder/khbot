import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# ទិន្នន័យ Bot ថ្មីរបស់អ្នក
BOT_TOKEN = "8872828720:AAGPmF_pexO7qeP7TKl_4cOxFGwz8OoQvRU"
BOT_USERNAME = "Happydownload_bot"
ADMIN_LINK = "https://t.me/heipko80"
START_IMAGE_URL = "https://i.supaimg.com/2c2963a3-a72b-47fd-ba30-ac78827d2091/cfa05bbb-5cf5-4780-a8fa-f85aa96202bb.jpg"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

USER_URLS = {}

async def send_welcome_menu(chat_id, context, user_first_name):
    welcome_text = (
        f"✨ **សួស្តី {user_first_name}!** ✨\n\n"
        "សូមស្វាគមន៍មកកាន់ **Video & MP3 Downloader Bot** 🎬🎵\n"
        "───────────────────\n"
        "📥 **របៀបទាញយក៖**\n"
        "១. ចម្លង (Copy) Link ពី TikTok, Facebook, YouTube...\n"
        "២. ផ្ញើ (Paste) Link នោះមកកាន់ទីនេះ\n"
        "៣. ជ្រើសរើសទាញយកជា MP4 ឬ MP3 🚀"
    )
    keyboard = [[InlineKeyboardButton("💬 ទំនាក់ទំនង Admin", url=ADMIN_LINK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=START_IMAGE_URL, 
        caption=welcome_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await send_welcome_menu(update.effective_chat.id, context, user.first_name)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ សូមផ្ញើ Link ឱ្យបានត្រឹមត្រូវ (ឧទាហរណ៍៖ https://...)")
        return

    USER_URLS[user_id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎬 Video (MP4)", callback_data="dl_video"),
            InlineKeyboardButton("🎵 Audio (MP3)", callback_data="dl_audio")
        ],
        [
            InlineKeyboardButton("❌ បោះបង់ / ចាប់ផ្តើមថ្មី", callback_data="cancel_action")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👇 សូមជ្រើសរើសប្រភេទឯកសារដែលអ្នកចង់ទាញយក៖", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "cancel_action":
        if user_id in USER_URLS:
            del USER_URLS[user_id]
        await query.delete_message()
        await send_welcome_menu(query.message.chat_id, context, query.from_user.first_name)
        return

    if query.data in ["like", "dislike"]:
        msg = "❤️ អរគុណសម្រាប់ការគាំទ្រ!" if query.data == "like" else "អរគុណសម្រាប់មតិ! យើងនឹងអភិវឌ្ឍបន្ថែមទៀត។"
        await query.answer(msg, show_alert=True)
        return

    url = USER_URLS.get(user_id)
    if not url:
        await query.edit_message_text("❌ ផុតកំណត់រង់ចាំ! សូមផ្ញើ Link ម្ដងទៀត។")
        return

    download_type = query.data
    await query.edit_message_text("⏳ កំពុងដំណើរការទាញយក សូមរង់ចាំមួយភ្លែត...")

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    if download_type == "dl_video":
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'downloads/{user_id}_%(id)s.%(ext)s',
            'max_filesize': 1500 * 1024 * 1024,
            'quiet': True,
        }
    else: # MP3
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'downloads/{user_id}_%(id)s.%(ext)s',
            'max_filesize': 1500 * 1024 * 1024,
            'quiet': True,
        }

    try:
        loop = asyncio.get_event_loop()
        filename = await loop.run_in_executor(None, download_file_sync, ydl_opts, url)

        await query.edit_message_text("📤 កំពុងបញ្ជូនឯកសារទៅ Telegram...")
        
        caption_text = (
            "✅ **បាន Download ដោយជោគជ័យ!**\n\n"
            f"🤖 ទាញយកតាមរយៈ៖ @{BOT_USERNAME}"
        )

        keyboard = [
            [
                InlineKeyboardButton("👍 ចូលចិត្ត", callback_data="like"),
                InlineKeyboardButton("👎 មិនចូលចិត្ត", callback_data="dislike")
            ],
            [
                InlineKeyboardButton("🔄 ទាញយកវីដេអូផ្សេងទៀត", callback_data="cancel_action")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        with open(filename, 'rb') as file:
            if download_type == "dl_video":
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=file,
                    caption=caption_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=file,
                    caption=caption_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )

        if os.path.exists(filename):
            os.remove(filename)
        await query.delete_message()

    except Exception as e:
        logging.error(f"Error downloading: {e}")
        await query.edit_message_text(
            "❌ មិនអាចទាញយកបានទេ!\n"
            "💡 ប្រសិនបើទាញយក MP3 មិនបាន សូមប្រាកដថាម៉ាស៊ីនរបស់អ្នកបានដំឡើង FFmpeg រួចរាល់។"
        )

def download_file_sync(ydl_opts, url):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def main():
    app = Application.builder().token(BOT_TOKEN).read_timeout(300).write_timeout(300).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot ត្រូវបានចាប់ផ្ដើមដំណើរការ...")
    app.run_polling()

if __name__ == '__main__':
    main()
