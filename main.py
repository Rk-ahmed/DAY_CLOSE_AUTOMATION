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
    NoSuchElementException,
    WebDriverException
)

# ---------------- CONFIG ----------------
URL = "https://sandboxerp.shakti.org.bd:8072/Home/Login?ReturnUrl=%2F"
CSV_FILE = "creds3.csv"
WAIT_TIME = 8            # general wait for elements
SHORT_WAIT = 2           # short wait for quick things
INITIAL_POPUP_WAIT = 5  # wait for homepage/modal to appear after login

# ---------------- DRIVER CREATION ----------------
def create_driver(use_temp_profile=True):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Password manager blocking
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
    """Quit driver and remove temporary profile dir if created."""
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

# ---------------- POPUP / MODAL HELPERS ----------------
def try_dismiss_google_password_popup_once(driver):
    """
    Try to dismiss Chrome / Google password popup — do this only once after login.
    Uses ESC then a click on body offset as fallback.
    """
    try:
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.2)
        # try click on body offset to remove overlays
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            actions.move_to_element_with_offset(body, 50, 50).click().perform()
        except Exception:
            pass
        print("✓ Sent ESC and attempted click to dismiss browser popups")
    except Exception as e:
        print(f"Note: dismiss attempt failed: {e}")

def click_ok_button_if_present(driver, timeout=3):
    """
    Try a short list of candidate XPaths for an 'OK' or response modal button.
    Returns True if clicked.
    """
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
            print(f"✓ Clicked modal button (xpath: {xpath})")
            # wait briefly for modal to go
            WebDriverWait(driver, 4).until(EC.invisibility_of_element_located((By.XPATH, '//*[@id="responseModal"]')))
            return True
        except (TimeoutException, NoSuchElementException):
            continue
    return False

def handle_initial_popups(driver):
    """
    Single place to handle initial popups / browser password suggestions / ERP warning modal.
    Call once immediately after login/homepage has loaded.
    """
    print("Checking for initial popups/modals...")
    # 1) Dismiss possible Chrome/Google password bubble
    try_dismiss_google_password_popup_once(driver)

    # 2) Wait briefly for potential ERP modal to appear then try clicking OK
    try:
        # If responseModal exists and is displayed, handle it
        modal = WebDriverWait(driver, INITIAL_POPUP_WAIT).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="responseModal"]'))
        )
        # Confirm it's visible then click OK via helper
        if modal and modal.is_displayed():
            print("⚠ ERP response modal detected on homepage")
            clicked = click_ok_button_if_present(driver, timeout=4)
            if not clicked:
                print("⚠ Couldn't click OK via primary selector — trying fallback explicit click")
                # fallback: try generic button inside modal
                try:
                    fallback_btn = modal.find_element(By.XPATH, './/button[contains(normalize-space(.),"Ok") or contains(normalize-space(.),"OK") or contains(normalize-space(.),"Yes")]')
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fallback_btn)
                    driver.execute_script("arguments[0].click();", fallback_btn)
                    WebDriverWait(driver, 4).until(EC.invisibility_of_element_located((By.XPATH, '//*[@id="responseModal"]')))
                    print("✓ Fallback clicked modal button")
                except Exception:
                    print("⚠ Fallback click failed")
    except TimeoutException:
        # No modal found in the initial wait window; that's fine.
        print("No ERP modal appeared on homepage.")

# ---------------- NAVIGATION / ACTIONS ----------------
def login(driver, username, password):
    """Enter credentials and submit login form (no repeated popup handling here)."""
    print(f"Logging in as {username}...")
    wait = WebDriverWait(driver, WAIT_TIME)

    username_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="emailaddress"]')))
    username_field.clear()
    username_field.send_keys(username)
    # small gentle pause to mimic human typing (optional)
    time.sleep(0.15)

    password_field = driver.find_element(By.XPATH, '//*[@id="password"]')
    password_field.clear()
    password_field.send_keys(password)
    time.sleep(0.15)

    # Click login
    login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/section/div[2]/div/div/div/form/div[5]/button')))
    driver.execute_script("arguments[0].click();", login_btn)
    print("✓ Login submitted")

def navigate_to_day_info(driver):
    """Navigate to MIS → Day Information (assumes homepage state)."""
    wait = WebDriverWait(driver, WAIT_TIME)
    print("Navigating to MIS → Day Information...")
    # click MIS menu
    mis_menu = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="homePage"]/div[1]/div/div[1]/div[7]/a/div/div/p')))
    driver.execute_script("arguments[0].click();", mis_menu)
    # click Day Information
    day_info = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="02"]/div[2]/div/div[2]/div/ul/li[1]/a')))
    driver.execute_script("arguments[0].click();", day_info)
    # wait for Day Information panel to appear
    WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.XPATH, '//*[@id="day-information"]')))
    print("✓ Navigated to Day Information")

def perform_day_open_or_close(driver):
    """
    On Day Information page, click whichever of Day Open / Day Close is available.
    Then handle the confirmation and response modal (Yes → OK).
    """
    wait = WebDriverWait(driver, WAIT_TIME)
    print("Performing available Day Open/Close action...")

    # Try Day Open first
    open_xpath = '//*[@id="day-information"]/div[1]/div/div/div[3]/div/button'
    close_xpath = '//*[@id="day-information"]/div[1]/div/div/div[3]/div/button[2]'

    action_taken = False
    try:
        open_btn = driver.find_element(By.XPATH, open_xpath)
        if open_btn.is_displayed() and open_btn.is_enabled():
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", open_btn)
            driver.execute_script("arguments[0].click();", open_btn)
            print("✓ Clicked Day Open")
            action_taken = True
    except NoSuchElementException:
        pass

    # If not opened, try close
    if not action_taken:
        try:
            close_btn = driver.find_element(By.XPATH, close_xpath)
            if close_btn.is_displayed() and close_btn.is_enabled():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_btn)
                driver.execute_script("arguments[0].click();", close_btn)
                print("✓ Clicked Day Close")
                action_taken = True
        except NoSuchElementException:
            pass

    if not action_taken:
        print("⚠ Neither Day Open nor Day Close button available.")
        return False

    # Wait for confirmation modal (day close confirmation or similar) and click Yes/Confirm
    try:
        # common confirm button xpath — try multiple candidates
        confirm_xpath_candidates = [
            '//*[@id="dayCloseConfirmation"]/div/div/div[3]/button[2]',  # DayClose specific
            '//div[@id="dayCloseConfirmation"]//button[contains(normalize-space(.),"Yes") or contains(normalize-space(.),"OK") or contains(normalize-space(.),"Confirm")]',
            '//button[contains(normalize-space(.),"Yes")]',
            '//button[contains(normalize-space(.),"Confirm")]',
        ]
        confirmed = False
        for cxpath in confirm_xpath_candidates:
            try:
                confirm_btn = WebDriverWait(driver, SHORT_WAIT).until(EC.element_to_be_clickable((By.XPATH, cxpath)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", confirm_btn)
                driver.execute_script("arguments[0].click();", confirm_btn)
                print(f"✓ Clicked confirmation button (xpath: {cxpath})")
                confirmed = True
                break
            except TimeoutException:
                continue

        if not confirmed:
            print("⚠ Confirmation button not found (maybe no confirm needed).")
    except Exception as e:
        print(f"Error while confirming action: {e}")

    # Wait & handle the response modal that shows result (OK)
    try:
        # Wait briefly for response modal to appear and handle it with helper
        time.sleep(0.5)
        if click_ok_button_if_present(driver, timeout=4):
            print("✓ Response modal handled after action")
        else:
            print("No response modal or could not auto-click it.")
    except Exception as e:
        print(f"While handling response modal: {e}")
    return True

# ---------------- MAIN FLOW ----------------
def main():
    print("=" * 60)
    print("Starting ERP Automation Script (optimized)")
    print("=" * 60)

    with open(CSV_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            username = row.get('username')
            password = row.get('password')
            if not username or not password:
                print("Skipping row with missing creds")
                continue

            print(f"\n{'=' * 60}")
            print(f"Processing user: {username}")
            print(f"{'=' * 60}")

            driver = create_driver(use_temp_profile=True)
            try:
                driver.get(URL)

                # login (enter credentials & submit)
                login(driver, username, password)

                # After submitting login, wait for a sign that homepage loaded.
                # You can tweak the element used here to one that reliably appears on home.
                try:
                    # Wait for an element that exists on homepage - adjust selector if needed
                    # Using the MIS menu selector as a homepage arrival indicator
                    WebDriverWait(driver, INITIAL_POPUP_WAIT).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="homePage"]/div[1]/div/div[1]/div[7]/a/div/div/p'))
                    )
                    print("✓ Homepage appeared")
                except TimeoutException:
                    print("⚠ Homepage did not appear within expected time — continuing anyway")

                # SINGLE initial popup handling (only once)
                handle_initial_popups(driver)

                # Now navigate and perform actions (modals handled only where necessary)
                try:
                    navigate_to_day_info(driver)
                    perform_day_open_or_close(driver)
                    print(f"\n✓✓✓ Completed actions for {username} ✓✓✓")
                except Exception as e:
                    print(f"Error during navigation/actions: {e}")

            except Exception as e:
                print(f"\n✗✗✗ Error with {username}: {e} ✗✗✗")
                import traceback
                traceback.print_exc()
            finally:
                cleanup_driver(driver)
                print(f"\n{'=' * 60}")
                print(f"Finished session for {username}")
                print(f"{'=' * 60}\n")
                # small pause between users to be a bit polite to the site
                time.sleep(0.6)

if __name__ == "__main__":
    main()