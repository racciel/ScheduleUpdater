import os
import time
import shutil
import subprocess
from zlib import crc32
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("FILE_URL")

DOWNLOAD_DIR = os.path.abspath("./download/")
LATEST_DOCX_DIR = os.path.abspath("./download/latest-docx/")
LATEST_PDF_DIR = os.path.abspath("./download/latest-pdf/")

os.makedirs(LATEST_DOCX_DIR, exist_ok=True)
os.makedirs(LATEST_PDF_DIR, exist_ok=True)

options = webdriver.FirefoxOptions()
options.add_argument("--headless")
options.set_preference("browser.download.folderList", 2)
options.set_preference("browser.download.dir", DOWNLOAD_DIR)
options.set_preference(
    "browser.helperApps.neverAsk.saveToDisk",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)

service = Service(os.getenv("GECKODRIVER_PATH"), log_path="/dev/null")  # Suppress Geckodriver logs
driver = webdriver.Firefox(service=service, options=options)

def compute_crc32(file_path):
    """Compute the CRC32 checksum of a file."""
    prev = 0
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            prev = crc32(chunk, prev)
    return f"{prev & 0xFFFFFFFF:08x}"

def delete_file(file_path):
    """Delete a file if it exists."""
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted file: {file_path}")

def handle_new_docx(downloaded_file):
    """Handle the new .docx file based on content changes."""
    latest_docx_file = os.path.join(LATEST_DOCX_DIR, "schedule.docx")

    if os.path.exists(latest_docx_file):
        old_crc = compute_crc32(latest_docx_file)
        new_crc = compute_crc32(downloaded_file)

        if old_crc == new_crc:
            print("No change detected in the document, deleting downloaded file.")
            delete_file(downloaded_file)
            return False
        else:
            delete_file(latest_docx_file)
            shutil.move(downloaded_file, latest_docx_file)
            print("Content changed, replaced the old .docx file.")
            return True
    else:
        shutil.move(downloaded_file, latest_docx_file)
        print("No previous .docx file, saved the new one.")
        return True

def handle_pdf_conversion():
    """Check if the latest-pdf folder is empty and convert the .docx to .pdf if needed."""
    if not os.listdir(LATEST_PDF_DIR):
        print("No PDF files found in the latest-pdf folder, converting the document to PDF.")
        latest_docx_file = os.path.join(LATEST_DOCX_DIR, "schedule.docx")
        pdf_file = convert_docx_to_pdf_libreoffice(latest_docx_file)
        if pdf_file:
            shutil.move(pdf_file, LATEST_PDF_DIR)
            print(f"PDF file created and moved to {LATEST_PDF_DIR}.")
    else:
        print("PDF folder is not empty, no conversion needed.")

def download_schedule():
    """Download the schedule document."""
    try:
        driver.get(URL)
        print("Page loaded. Waiting for content...")

        wait = WebDriverWait(driver, 30)
        iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        print("Iframe detected. Switching context...")

        driver.switch_to.frame(iframe)

        download_button = wait.until(EC.presence_of_element_located((By.ID, "DownloadADocumentCopy")))
        print("Download button found inside iframe.")

        print("Attempting to trigger download via JavaScript...")
        driver.execute_script("arguments[0].click();", download_button)

        print("Waiting for the file to be downloaded...")
        downloaded_file = wait_for_file(DOWNLOAD_DIR, timeout=120)

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

def wait_for_file(download_dir, timeout=120):
    """Wait for a new file to appear in the directory."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        files = os.listdir(download_dir)
        if files:
            files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(download_dir, x)), reverse=True)
            newest_file = os.path.join(download_dir, files[0])
            if os.path.isfile(newest_file):
                return newest_file
        time.sleep(1)
    return None