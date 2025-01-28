import os
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, ElementNotInteractableException
import time

# Path to the folder containing your images
IMAGE_FOLDER = "C:\\Users\\arslan\\Videos\\ai\\ai\\New folder\\Minimalist Poster\\Anime\\Filtered Posters\\ByYear\\2024"
LOG_FILE = "processed_images.log"
SESSION_LOG_FILE = "session.log"
FAILED_LOG_FILE = "failed_images.log"

# Pinterest Pin details
TITLE = "Anime Minimalist Poster"
DESCRIPTION = "Find minimalist posters for your favorite anime series. Follow us for more updates."
BOARD_NAME = "Anime Minimalist Poster By Years"  # Your board name
SECTION_NAME = "2024"  # Optional: section name
LINK = "https://discord.gg/UeeEj6nhkD"  # Optional: link to your website

# Path to your Chrome user data directory
USER_DATA_DIR = os.path.join(os.getcwd(), "PinterestSession")

# Set up the WebDriver to use a persistent context
options = uc.ChromeOptions()
options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = uc.Chrome(options=options)

# Open Pinterest
driver.get("https://www.pinterest.com/")

# Wait for the page to load (adjust time if needed)
time.sleep(5)

# Check if the user is logged in
def check_login():
    if not os.path.exists(SESSION_LOG_FILE):
        with open(SESSION_LOG_FILE, "w") as f:
            f.write("not_logged_in")

    with open(SESSION_LOG_FILE, "r") as f:
        status = f.read().strip()

    if status == "not_logged_in":
        print("Please log in to Pinterest and press Enter to continue...")
        input()
        with open(SESSION_LOG_FILE, "w") as f:
            f.write("logged_in")

check_login()

# List of genres
GENRES = [
    "Action", "Adventure", "Avant_Garde", "Award_Winning", "Boys_Love", "Comedy", "Drama", "Ecchi", 
    "Erotica", "Fantasy", "Girls_Love", "Gourmet", "Hentai", "Horror", "Mystery", "Romance", "Sci-Fi", 
    "Slice_of_Life", "Sports", "Supernatural", "Suspense"
]

def retry_find_element(driver, by, value, delay=2):
    while True:
        try:
            element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except StaleElementReferenceException:
            print(f"Retrying to find element: {value}")
            time.sleep(delay)

def retry_interact_with_element(driver, by, value, interaction, delay=2):
    while True:
        try:
            element = retry_find_element(driver, by, value)
            interaction(element)
            return
        except (StaleElementReferenceException, ElementNotInteractableException):
            print(f"Retrying to interact with element: {value}")
            time.sleep(delay)

def load_processed_images(log_file):
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            return set(line.strip() for line in f)
    return set()

def save_processed_images(log_file, images):
    with open(log_file, "a") as f:
        for image in images:
            f.write(f"{image}\n")

def save_failed_images(log_file, images):
    with open(log_file, "a") as f:
        for image in images:
            f.write(f"{image}\n")

def generate_title(image_file):
    # Remove the MAL ID, year, genres, replace underscores with spaces, and remove the file extension
    parts = image_file.split('_')  # Split by underscore

    # Skip the MAL ID (first part) and year (second part) if they exist
    title_parts = []
    for part in parts[2:]:
        if part in GENRES or part.isdigit():  # Skip genres and numeric parts (like year)
            continue
        title_parts.append(part)

    title = ' '.join(title_parts).replace(".jpg", "").replace(".png", "").replace(".jpeg", "")
    title = f"{title} | Minimalist Poster | CogitoAnime"
    return title

def prompt_section_name():
    global SECTION_NAME
    try:
        retry_interact_with_element(driver, By.CSS_SELECTOR, "button[data-test-id='board-dropdown-select-button']", lambda e: e.click())
        time.sleep(2)
        has_sections = driver.find_elements(By.CSS_SELECTOR, "div[data-test-id^='section-row']")
        if has_sections:
            SECTION_NAME = input("Enter the section name for the board: ").strip()
    except Exception as e:
        print(f"Error checking for sections: {e}")

def process_images(driver, image_files, processed_images, new_processed_images, failed_images):
    for image_file in image_files:
        if len(new_processed_images) >= 20:
            break

        if image_file in processed_images:
            print(f"Skipping already processed image: {image_file}")
            continue

        if image_file.endswith(('.jpg', '.png', '.jpeg')):  # Only process image files
            image_path = os.path.join(IMAGE_FOLDER, image_file)

            # Generate title
            title = generate_title(image_file)

            # Navigate to the Pin creation page
            if len(new_processed_images) <= 2:
                driver.get("https://www.pinterest.com/pin-creation-tool/")
                time.sleep(5)

            # Upload the image
            upload_attempts = 0
            while upload_attempts < 3:
                try:
                    retry_interact_with_element(driver, By.CSS_SELECTOR, "input[data-test-id='storyboard-upload-input']", lambda e: e.send_keys(image_path))
                    break
                except Exception as e:
                    upload_attempts += 1
                    print(f"Error uploading image (attempt {upload_attempts}): {e}")
                    time.sleep(2)
                    if upload_attempts == 3:
                        print(f"Failed to upload image after 3 attempts: {image_file}")
                        failed_images.append(image_file)
                        continue

            if upload_attempts == 3:
                continue

            # Wait for the image thumbnail to be visible
            while True:
                try:
                    retry_find_element(driver, By.CSS_SELECTOR, "div[data-test-id='storyboard-thumbnail']")
                    break
                except Exception as e:
                    print(f"Error waiting for thumbnail: {e}")
                    time.sleep(2)

            # Add Title
            while True:
                try:
                    retry_interact_with_element(driver, By.ID, "storyboard-selector-title", lambda e: e.clear())
                    retry_interact_with_element(driver, By.ID, "storyboard-selector-title", lambda e: e.send_keys(title))
                    break
                except Exception as e:
                    print(f"Error adding title: {e}")
                    time.sleep(2)

            # Add Description
            while True:
                try:
                    retry_interact_with_element(driver, By.CSS_SELECTOR, "div[data-test-id='editor-with-mentions'] div[contenteditable='true']", lambda e: e.clear())
                    retry_interact_with_element(driver, By.CSS_SELECTOR, "div[data-test-id='editor-with-mentions'] div[contenteditable='true']", lambda e: e.send_keys(DESCRIPTION))
                    break
                except Exception as e:
                    print(f"Error adding description: {e}")
                    time.sleep(2)

            # Add Destination Link
            while True:
                try:
                    retry_interact_with_element(driver, By.ID, "WebsiteField", lambda e: e.clear())
                    retry_interact_with_element(driver, By.ID, "WebsiteField", lambda e: e.send_keys(LINK))
                    break
                except Exception as e:
                    print(f"Error adding destination link: {e}")
                    time.sleep(2)

            # Select Board
            while True:
                try:
                    retry_interact_with_element(driver, By.CSS_SELECTOR, "button[data-test-id='board-dropdown-select-button']", lambda e: e.click())
                    retry_interact_with_element(driver, By.CSS_SELECTOR, f"div[data-test-id='board-row-{BOARD_NAME}']", lambda e: e.click())
                    break
                except Exception as e:
                    print(f"Error selecting board: {e}")
                    time.sleep(2)

            # Select Section (if applicable)
            if SECTION_NAME:
                while True:
                    try:
                        retry_interact_with_element(driver, By.CSS_SELECTOR, f"div[data-test-id='section-row-{SECTION_NAME}']", lambda e: e.click())
                        break
                    except Exception as e:
                        print(f"Error selecting section: {e}")
                        time.sleep(2)

            # Wait for 3 seconds after selecting the section
            time.sleep(5)

            # Add the image to the list of processed images
            new_processed_images.append(image_file)

            # Click the "Create new" button after the first 2 images
            if len(new_processed_images) > 2:
                while True:
                    try:
                        retry_interact_with_element(driver, By.CSS_SELECTOR, "div[data-test-id='storyboard-create-button'] button", lambda e: e.click())
                        break
                    except Exception as e:
                        print(f"Error clicking 'Create new' button: {e}")
                        time.sleep(2)

# Load processed images
processed_images = load_processed_images(LOG_FILE)

# Prompt for section name if necessary
prompt_section_name()

# Process images
new_processed_images = []
failed_images = []
process_images(driver, os.listdir(IMAGE_FOLDER), processed_images, new_processed_images, failed_images)

# Prompt user to publish manually
print("Please publish the pins manually and press Enter to continue...")
input()

# Save the processed images to the log file
save_processed_images(LOG_FILE, new_processed_images)

# Save the failed images to the log file
save_failed_images(FAILED_LOG_FILE, failed_images)

# Show message when all images are published
print(f"Processed {len(new_processed_images)} images.")
input("Press Enter to exit...")
