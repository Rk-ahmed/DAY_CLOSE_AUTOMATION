import csv
import time
import tempfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException
)

# ---------------- CONFIG ----------------
URL = "https://sandboxerp.shakti.org.bd:8072/Home/Login?ReturnUrl=%2F"
CSV_FILE = "creds3.csv"
WAIT_TIME = 8
SHORT_WAIT = 2
INITIAL_POPUP_WAIT = 5

# ---------------- DRIVER ----------------
def create_driver(use_temp_profile=True):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-save-password-bubble")
    options.add_argument("--password-store=basic")
    options.add_argument("--disable-features=PasswordLeakDetection,SyncCredentialManager,PasswordManagerOnboarding,AutofillServerCommunication,PasswordManager")
    options.add_argument("--disable-password-manager-reauthentication")
    options.add_argument("--incognito")

    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 0,
        "autofill.profile_enabled": False,
        "password_manager_enabled": False,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)

    temp_dir = None
    if use_temp_profile:
        temp_dir = tempfile.mkdtemp(prefix="chrome-temp-profile-")
        options.add_argument(f"--user-data-dir={temp_dir}")

    driver = webdriver.Chrome(options=options)
    driver._temp_user_data_dir = temp_dir
    return driver

def cleanup_driver(driver):
    try:
        temp_dir = getattr(driver, "_temp_user_data_dir", None)
        driver.quit()
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Could not remove temp profile dir: {e}")
    except Exception as e:
        print(f"Error quitting driver: {e}")

# ---------------- POPUPS ----------------
def try_dismiss_google_password_popup_once(driver):
    try:
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.2)
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            actions.move_to_element_with_offset(body, 50, 50).click().perform()
        except Exception:
            pass
    except Exception as e:
        print(f"Note: dismiss attempt failed: {e}")

def click_ok_button_if_present(driver, timeout=3):
    ok_button_xpaths = [
        '//*[@id="responseModal"]/div/div/div[3]/button',
        '//button[contains(@class, "btn-outline-warning") and contains(normalize-space(.),"Ok")]',
        '//button[contains(normalize-space(.),"Ok")]',
        '//button[contains(normalize-space(.),"OK")]',
        '//button[contains(normalize-space(.),"Yes")]',
    ]
    for xpath in ok_button_xpaths:
        try:
            btn = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(0.15)
            driver.execute_script("arguments[0].click();", btn)
            WebDriverWait(driver, 4).until(EC.invisibility_of_element_located((By.XPATH, '//*[@id="responseModal"]')))
            return True
        except (TimeoutException, NoSuchElementException):
            continue
    return False

def handle_initial_popups(driver):
    try_dismiss_google_password_popup_once(driver)
    try:
        modal = WebDriverWait(driver, INITIAL_POPUP_WAIT).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="responseModal"]'))
        )
        if modal and modal.is_displayed():
            clicked = click_ok_button_if_present(driver, timeout=4)
            if not clicked:
                try:
                    fallback_btn = modal.find_element(By.XPATH, './/button[contains(normalize-space(.),"Ok") or contains(normalize-space(.),"OK") or contains(normalize-space(.),"Yes")]')
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fallback_btn)
                    driver.execute_script("arguments[0].click();", fallback_btn)
                    WebDriverWait(driver, 4).until(EC.invisibility_of_element_located((By.XPATH, '//*[@id="responseModal"]')))
                except Exception:
                    pass
    except TimeoutException:
        pass

# ---------------- LOGIN ----------------
def login(driver, username, password):
    wait = WebDriverWait(driver, WAIT_TIME)
    username_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="emailaddress"]')))
    username_field.clear()
    username_field.send_keys(username)
    time.sleep(0.15)

    password_field = driver.find_element(By.XPATH, '//*[@id="password"]')
    password_field.clear()
    password_field.send_keys(password)
    time.sleep(0.15)

    login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/section/div[2]/div/div/div/form/div[5]/button')))
    driver.execute_script("arguments[0].click();", login_btn)

# ---------------- DAY CLOSE ----------------
def perform_direct_day_close(driver):
    wait = WebDriverWait(driver, WAIT_TIME)
    try:
        day_close_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="day-information"]/div[1]/div/div/div[3]/div/button[2]')))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", day_close_btn)
        driver.execute_script("arguments[0].click();", day_close_btn)
        print("✓ Clicked Day Close")

        confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dayCloseConfirmation"]/div/div/div[3]/button[2]')))
        driver.execute_script("arguments[0].click();", confirm_btn)
        print("✓ Confirmed Day Close")

        click_ok_button_if_present(driver, timeout=5)
        print("✓ Response modal handled")
        return True
    except Exception as e:
        print(f"⚠ Day Close failed: {e}")
        return False

# ---------------- MAIN ----------------
def main():
    with open(CSV_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            username = row.get('username')
            password = row.get('password')
            if not username or not password:
                continue

            print(f"\n=== Processing user: {username} ===")
            driver = create_driver(use_temp_profile=True)
            try:
                driver.get(URL)
                login(driver, username, password)
                try:
                    WebDriverWait(driver, INITIAL_POPUP_WAIT).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="homePage"]/div[1]/div/div[1]/div[7]/a/div/div/p'))
                    )
                except TimeoutException:
                    print("⚠ Homepage may not have fully loaded")

                handle_initial_popups(driver)
                perform_direct_day_close(driver)

            except Exception as e:
                print(f"✗ Error for {username}: {e}")
            finally:
                cleanup_driver(driver)
                print(f"=== Finished session for {username} ===\n")
                time.sleep(0.6)

if __name__ == "__main__":
    main()