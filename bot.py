import asyncio
import base64
import requests
import zipfile
import tempfile
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ===================== CONFIG =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITHUB_USERNAME = "kanhucharanapradhanytpremium-wq"
REPO_NAME = "telegram-html-hosting"

OWNER_ID = 5885532013
OWNER_ONLY = false
# =================================================

GITHUB_API = "https://api.github.com"


def is_allowed(update: Update) -> bool:
    if not OWNER_ONLY:
        return True
    return update.effective_user.id == OWNER_ID


# ===================== COMMANDS =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("❌ Access denied. Owner only bot.")
        return

    msg = (
        f"👋 Hello, {update.effective_user.first_name}!\n\n"
        "Welcome to the Telegram HTML Hosting Bot 🚀\n\n"
        "Upload an HTML file or ZIP (HTML + CSS + JS)\n"
        "and I will host it on GitHub Pages.\n\n"
        "📌 Commands:\n"
        "/help - Guide\n"
        "/about - About bot\n"
        "/stats - Bot stats\n"
        "/delete - Delete website\n"
    )
    await update.message.reply_text(msg)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("❌ Access denied.")
        return

    await update.message.reply_text(
        "📌 HOW TO USE\n\n"
        "1️⃣ Send index.html OR a ZIP file\n"
        "2️⃣ Bot uploads it to GitHub Pages\n"
        "3️⃣ You get a live website link\n\n"
        "❗ Static sites only (HTML/CSS/JS)"
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("❌ Access denied.")
        return

    await update.message.reply_text(
        "<b>👨‍💻 About This Bot</b>\n\n"
        "<b>🤖 Name:</b> Telegram HTML Hosting Bot\n\n"
        "<b>✨ Description:</b>\n"
        "Create a <b>FREE live website</b> by uploading\n"
        "an HTML file or ZIP directly on Telegram.\n\n"
        "<b>🛠️ Developer:</b>\n"
        "Kanhu Charan Pradhan\n"
        "<a href='https://t.me/KanhuCharanaPradhan'>@KanhuCharanaPradhan</a>\n\n"
        "<b>⚡ Powered By:</b>\n"
        "Python + Telegram Bot API\n"
        "GitHub Pages\n",
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("❌ Access denied.")
        return

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"{GITHUB_API}/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/"
    r = requests.get(url, headers=headers)

    folders = [
        i for i in r.json()
        if i["type"] == "dir" and i["name"].startswith("user_")
    ]

    await update.message.reply_text(
        f"📊 Bot Stats\n\n"
        f"👥 Users: {len(folders)}\n"
        f"🌐 Websites: {len(folders)}"
    )


async def delete_site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("❌ Access denied.")
        return

    user_id = update.effective_user.id
    path = f"user_{user_id}/index.html"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    get_url = f"{GITHUB_API}/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{path}"
    r = requests.get(get_url, headers=headers)

    if r.status_code != 200:
        await update.message.reply_text("❌ No website found.")
        return

    sha = r.json()["sha"]

    requests.delete(
        get_url,
        headers=headers,
        json={"message": "Delete website", "sha": sha}
    )

    await update.message.reply_text("✅ Website deleted.")


# ===================== FILE UPLOAD =====================

async def upload_html(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("❌ Access denied.")
        return

    doc = update.message.document
    if not doc.file_name.endswith(".html"):
        await update.message.reply_text("❌ Only .html allowed.")
        return

    user_id = update.effective_user.id
    folder = f"user_{user_id}"

    tg_file = await doc.get_file()
    local_path = tempfile.mktemp(suffix=".html")
    await tg_file.download_to_drive(local_path)

    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"{GITHUB_API}/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{folder}/index.html"

    requests.put(
        url,
        headers=headers,
        json={"message": "Upload HTML", "content": content}
    )

    site = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/{folder}/"
    await update.message.reply_text(f"✅ Website live:\n{site}")


async def upload_zip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        await update.message.reply_text("❌ Access denied.")
        return

    doc = update.message.document
    if not doc.file_name.endswith(".zip"):
        await update.message.reply_text("❌ Only .zip allowed.")
        return

    user_id = update.effective_user.id
    folder = f"user_{user_id}"

    tg_file = await doc.get_file()
    zip_path = tempfile.mktemp(suffix=".zip")
    await tg_file.download_to_drive(zip_path)

    extract_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_dir)

    if "index.html" not in os.listdir(extract_dir):
        await update.message.reply_text("❌ index.html missing in ZIP.")
        return

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    for root, _, files in os.walk(extract_dir):
        for file in files:
            path = os.path.join(root, file)
            rel = os.path.relpath(path, extract_dir)

            with open(path, "rb") as f:
                content = base64.b64encode(f.read()).decode()

            url = f"{GITHUB_API}/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{folder}/{rel}"
            requests.put(
                url,
                headers=headers,
                json={"message": f"Upload {rel}", "content": content}
            )

    site = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/{folder}/"
    await update.message.reply_text(f"✅ ZIP website live:\n{site}")


# ===================== MAIN =====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("delete", delete_site))

    app.add_handler(MessageHandler(filters.Document.FileExtension("html"), upload_html))
    app.add_handler(MessageHandler(filters.Document.FileExtension("zip"), upload_zip))

    print("🤖 Bot is running on Railway...")
    app.run_polling()


if __name__ == "__main__":
    main()