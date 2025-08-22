import discord
from discord.ext import commands, tasks
import requests
import os
from dotenv import load_dotenv
import webserver

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)

REDIRECTOR_URL = "https://mitlogs-links.onrender.com"
SELF_URL = "https://mitlogs-links-iyrf.onrender.com"  

@tasks.loop(minutes=14.5)
async def keep_awake():
    try:
        res = requests.get(SELF_URL, timeout=10)
        print(f"[KeepAlive] Pinged self, status: {res.status_code}")
    except Exception as e:
        print(f"[KeepAlive] Error pinging self: {e}")


@bot.event
async def on_ready():
    print(f"{bot.user} is online and running!")
    if not keep_awake.is_running():
        keep_awake.start()  # start background pinger

@bot.command()
async def shorten(ctx, short_id: str, url: str):
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {"id": short_id, "url": url}
        print(f"Sending request to {REDIRECTOR_URL}/create")
        print(f"Payload: {payload}")
        
        response = requests.post(
            f"{REDIRECTOR_URL}/create",
            json=payload,
            headers=headers,
            timeout=100
        )
        
        if response.status_code in (200, 201):
            data = response.json()
            message = data.get("message", "")
            short_url = data.get("short_url")
            if message:
                await ctx.send(f"{message}\nNew link: {short_url}")
            else:
                await ctx.send(f"Created link: {short_url}")
        else:
            error_msg = f"Error {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('error', 'Unknown error')}"
            except:
                error_msg += f": {response.text}"
            await ctx.send(f"Failed to create shortened link. {error_msg}")
            
    except requests.exceptions.RequestException as e:
        await ctx.send(f"Error connecting to the redirector service: {str(e)}")
        print(f"Detailed error: {e}")
    except Exception as e:
        await ctx.send("An unexpected error occurred.")
        print(f"Unexpected error: {e}")


webserver.keep_alive()
bot.run(TOKEN)
