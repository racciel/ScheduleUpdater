import discord
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID")) # MUST BE AN INTEGER!!!
LATEST_PDF_DIR = "./download/latest-pdf"

intents = discord.Intents.default()
intents.message_content = True 

client = discord.Client(intents=intents)

async def send_file_to_discord(pdf_file_path):
    """Send the PDF to the Discord channel."""
    channel = client.get_channel(CHANNEL_ID)
    
    if channel is None:
        print(f"Error: Channel with ID {CHANNEL_ID} not found.")
        return
    
    with open(pdf_file_path, 'rb') as f:
        await channel.send(file=discord.File(f, os.path.basename(pdf_file_path)))
    print(f"File {pdf_file_path} sent to Discord.")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    pdf_file_path = os.path.join(LATEST_PDF_DIR, "schedule.pdf")
    
    if os.path.exists(pdf_file_path):
        await send_file_to_discord(pdf_file_path)
    else:
        print("No PDF file found to send.")    
    await client.close() 

#client.run(BOT_TOKEN)