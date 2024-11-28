import discord
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Replace with your Bot Token and channel ID
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Can be a text channel ID, as an integer
LATEST_PDF_DIR = "./download/latest-pdf"

# Define intents for your bot (this is required in newer versions of discord.py)
intents = discord.Intents.default()
intents.message_content = True  # Enable the 'message_content' intent

# Create the Discord client with intents
client = discord.Client(intents=intents)

async def send_file_to_discord(pdf_file_path):
    """Send the PDF to the Discord channel."""
    channel = client.get_channel(CHANNEL_ID)
    
    # Check if the channel is valid
    if channel is None:
        print(f"Error: Channel with ID {CHANNEL_ID} not found.")
        return
    
    with open(pdf_file_path, 'rb') as f:
        await channel.send(file=discord.File(f, os.path.basename(pdf_file_path)))
    print(f"File {pdf_file_path} sent to Discord.")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    
    # Send the file once bot is ready
    pdf_file_path = os.path.join(LATEST_PDF_DIR, "schedule.pdf")
    
    if os.path.exists(pdf_file_path):
        await send_file_to_discord(pdf_file_path)
    else:
        print("No PDF file found to send.")
    
    await client.close() 
    
# Run the bot
client.run(BOT_TOKEN)