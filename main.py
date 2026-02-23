from flask import Flask, request
import os
import asyncio
import threading
import discord
from discord import File, ForumChannel
from discord.ext import commands

# ==============================
# CONFIGURAÇÃO
# ==============================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BUG_FORUM_CHANNEL_ID = 1416931226899452047

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)
LOG_FOLDER = "logs"
os.makedirs(LOG_FOLDER, exist_ok=True)

# Evento para saber quando o bot está pronto
bot_ready = asyncio.Event()

# ==============================
# EVENTO ON_READY
# ==============================
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    bot_ready.set()

# ==============================
# FUNÇÃO DE ENVIO
# ==============================
async def send_bug_report(player_name: str, file_path: str):
    try:
        await bot_ready.wait()

        channel = bot.get_channel(BUG_FORUM_CHANNEL_ID)

        if channel is None:
            print("❌ Canal não encontrado! Verifique o ID.")
            return

        if not isinstance(channel, ForumChannel):
            print("❌ O canal não é um fórum!")
            return

        print("✅ Canal encontrado, enviando post...")

        with open(file_path, "rb") as f:
            discord_file = File(f, filename=os.path.basename(file_path))

            perms = channel.permissions_for(channel.guild.me)

            print("VIEW CHANNEL:", perms.view_channel)
            print("SEND MESSAGES:", perms.send_messages)
            print("CREATE PUBLIC THREADS:", perms.create_public_threads)
            print("ATTACH FILES:", perms.attach_files)
            print("SEND IN THREADS:", perms.send_messages_in_threads)
            print("MANAGE THREADS:", perms.manage_threads)

            await channel.create_thread(
                name=f"Bug enviado por: {player_name}",
                content=f"🐞 Bug report enviado pelo player **{player_name}**.",
                file=discord_file,
                applied_tags=[discord.Object(id=1464691989709848724)]
            )

        print("✅ Bug enviado para o Discord!")

        # Remove o arquivo apenas se envio foi sucesso
        os.remove(file_path)
        print("🗑 Arquivo removido do disco.")

    except Exception as e:
        print("❌ ERRO AO ENVIAR PARA O DISCORD:")
        print(e)

# ==============================
# ROTA FLASK
# ==============================
@app.route("/send_log", methods=["POST"])
def receive_log():
    data = request.json

    if not data or "log" not in data:
        return {"status": "error", "message": "No log found"}, 400

    player_name = data.get("player_name", "unknown")
    log_content = data["log"]

    filename = f"{player_name}_log.txt"
    filepath = os.path.join(LOG_FOLDER, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(log_content)

    print(f"📁 Log salvo em {filepath}")

    # Envia para o loop principal do bot
    bot.loop.call_soon_threadsafe(
    lambda: bot.loop.create_task(
        send_bug_report(player_name, filepath)
    )
)

    return {"status": "success", "message": "Log recebido"}, 200

# ==============================
# START
# ==============================
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)