import asyncio
from downloader import download_schedule, handle_new_docx, handle_pdf_conversion
from bot import client
import os
from dotenv import load_dotenv

load_dotenv()

LATEST_PDF_DIR = "./download/latest-pdf"
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def process_schedule():
    """Download and process the schedule only if it's new."""
    print("Starting the schedule update process...")

    # Step 1: Download the file
    downloaded_file = download_schedule()
    
    # Step 2: If no file is downloaded, exit
    if not downloaded_file:
        print("No file downloaded. Exiting...")
        return
    
    # Step 3: Check if the new file is different
    file_is_new = handle_new_docx(downloaded_file)
    if not file_is_new:
        print("No changes detected. Schedule remains unchanged.")
        return  # Exit if the file is unchanged
    else:
        print("New file detected. Processing the update...")
        # Step 4: Convert the new DOCX to PDF
        handle_pdf_conversion()

        # Step 5: Check if the PDF conversion succeeded
        latest_pdf = os.path.join(LATEST_PDF_DIR, "schedule.pdf")
        if os.path.exists(latest_pdf):
            print("New PDF generated. Sending to Discord...")
            await client.start(BOT_TOKEN)  # Updated to avoid asyncio.run() issue
        else:
            print("PDF conversion failed. File not sent.")

if __name__ == "__main__":
    asyncio.run(process_schedule())
