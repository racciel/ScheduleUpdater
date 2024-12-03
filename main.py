import os
import time
import asyncio
from downloader import handle_new_docx, handle_pdf_conversion, wait_for_file, compute_file_hash
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bot import send_file_to_discord
from dotenv import load_dotenv

load_dotenv()

CHECK_INTERVAL = 3600
URL = os.getenv("FILE_URL")
DOWNLOAD_DIR = os.path.abspath("./download/")
LATEST_DOCX_DIR = os.path.abspath("./download/latest-docx/")
LATEST_PDF_DIR = os.path.abspath("./download/latest-pdf/")
GECKODRIVER_PATH = os.getenv("GECKODRIVER_PATH")

options = webdriver.FirefoxOptions()
options.add_argument("--headless")
options.set_preference("browser.download.folderList", 2)
options.set_preference("browser.download.dir", DOWNLOAD_DIR)
options.set_preference(
    "browser.helperApps.neverAsk.saveToDisk",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)
service = Service(GECKODRIVER_PATH)


def download_schedule():
    """Download the schedule document."""
    driver = webdriver.Firefox(service=service, options=options)
    try:
        driver.get(URL)
        print("Page loaded. Waiting for content...")

        wait = WebDriverWait(driver, 20)
        iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        print("Iframe detected. Switching context...")

        driver.switch_to.frame(iframe)

        download_button = wait.until(EC.presence_of_element_located((By.ID, "DownloadADocumentCopy")))
        print("Download button found inside iframe.")

        print("Attempting to trigger download via JavaScript...")
        driver.execute_script("arguments[0].click();", download_button)

        print("Waiting for the file to be downloaded...")
        downloaded_file = wait_for_file(DOWNLOAD_DIR, timeout=60)

        if downloaded_file:
            print(f"File downloaded successfully: {downloaded_file}")
            return downloaded_file
        else:
            print("File download failed or timed out.")
            return None
    except Exception as e:
        print(f"Error encountered during download: {e}")
        return None
    finally:
        driver.quit()


async def check_and_send_update():
    """Check for updates and send the new schedule if available."""
    downloaded_file = download_schedule()

    if downloaded_file and handle_new_docx(downloaded_file):
        handle_pdf_conversion()
        latest_pdf = os.path.join(LATEST_PDF_DIR, "schedule.pdf")
        if os.path.exists(latest_pdf):
            print("New schedule detected. Sending to Discord...")
            await send_file_to_discord(latest_pdf)
        else:
            print("PDF conversion failed or file not found.")
    else:
        print("No updates detected.")


async def main():
    """Main loop to periodically check for updates."""
    while True:
        print("Checking for updates...")
        await check_and_send_update()
        print(f"Sleeping for {CHECK_INTERVAL} seconds...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
