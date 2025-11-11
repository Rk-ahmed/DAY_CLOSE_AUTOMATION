import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# ---------------- CONFIG ----------------
URL = "https://sandboxerp.shakti.org.bd:8072/Home/Login?ReturnUrl=%2F"
CSV_FILE = "creds3.csv"
WAIT_TIME = 10            # wait for page elements
POST_CONFIRM_WAIT = 10    # wait after clicking Yes
MAX_CONCURRENT_SESSIONS = 2
DAY_CLOSE_MAX_WAIT = 180
POLL_INTERVAL = 5

# ---------------- DRIVER ----------------
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver

# ---------------- LOGIN + DAY CLOSE FLOW ----------------
def run_single_session(username, password):
    start_time = time.time()
    print(f"\n[{username}] → Starting session")
    driver = create_driver()
    driver.get(URL)

    try:
        wait = WebDriverWait(driver, WAIT_TIME)

        # --- LOGIN ---
        username_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="emailaddress"]')))
        username_field.clear()
        username_field.send_keys(username)

        password_field = driver.find_element(By.XPATH, '//*[@id="password"]')
        password_field.clear()
        password_field.send_keys(password)

        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/section/div[2]/div/div/div/form/div[5]/button')))
        driver.execute_script("arguments[0].click();", login_btn)

        # --- WAIT FOR HOMEPAGE ---
        try:
            WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="homePage"]/div[1]/div/div[1]/div[7]/a/div/div/p'))
            )
            print(f"[{username}] Logged in successfully")
        except TimeoutException:
            print(f"[{username}] Homepage not detected but continuing")

        # --- NAVIGATE TO DAY INFORMATION ---
        mis_menu = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="homePage"]/div[1]/div/div[1]/div[7]/a/div/div/p')))
        driver.execute_script("arguments[0].click();", mis_menu)
        time.sleep(1.5)

        day_info = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="02"]/div[2]/div/div[2]/div/ul/li[1]/a')))
        driver.execute_script("arguments[0].click();", day_info)
        time.sleep(2)

        # --- CLICK DAY CLOSE BUTTON ---
        try:
            close_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="day-information"]/div[1]/div/div/div[3]/div/button'))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", close_btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", close_btn)
            print(f"[{username}] Clicked Day Close button")
        except (TimeoutException, NoSuchElementException):
            print(f"[{username}] ❌ No Day Close button found — possibly already closed")
            driver.quit()
            return

        # --- CLICK CONFIRMATION YES BUTTON ---
        try:
            print(f"[{username}] Waiting for confirmation modal...")
            yes_btn = WebDriverWait(driver, WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="dayOpenConfirmation"]/div/div/div[3]/button[2]'))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", yes_btn)
            time.sleep(0.8)
            driver.execute_script("arguments[0].click();", yes_btn)
            print(f"[{username}] ✅ Clicked confirmation 'Yes'")
        except (TimeoutException, ElementClickInterceptedException):
            # fallback
            try:
                time.sleep(2)
                yes_btn = driver.find_element(By.XPATH, '//*[@id="dayOpenConfirmation"]/div/div/div[3]/button[2]')
                driver.execute_script("arguments[0].click();", yes_btn)
                print(f"[{username}] ✅ Clicked confirmation 'Yes' (via fallback)")
            except Exception:
                print(f"[{username}] ❌ Could not click confirmation 'Yes'")

        # --- WAIT FOR CONFIRMATION SUCCESS ---
        time.sleep(POST_CONFIRM_WAIT)
        confirmed = False
        for _ in range(0, DAY_CLOSE_MAX_WAIT, POLL_INTERVAL):
            try:
                success_message = driver.find_elements(By.XPATH, "//div[contains(text(),'Day Closed Successfully')]")
                if success_message:
                    print(f"[{username}] ✅ Day Close confirmed via success message")
                    confirmed = True
                    break

                close_btn_check = driver.find_elements(By.XPATH, '//*[@id="day-information"]/div[1]/div/div/div[3]/div/button')
                if not close_btn_check or not close_btn_check[0].is_enabled():
                    print(f"[{username}] ✅ Day Close confirmed (button disappeared/disabled)")
                    confirmed = True
                    break
            except Exception:
                pass
            time.sleep(POLL_INTERVAL)

        if not confirmed:
            print(f"[{username}] ⚠ Day Close not confirmed — backend may still be processing")

        print(f"[{username}] ✓ Session completed in {time.time() - start_time:.2f}s")

    except Exception as e:
        print(f"[{username}] ✗ Error: {e}")

    finally:
        driver.quit()

# ---------------- MAIN ----------------
def main():
    users = []
    with open(CSV_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get("username") and row.get("password"):
                users.append((row["username"], row["password"]))

    print(f"Launching {len(users)} users with {MAX_CONCURRENT_SESSIONS} concurrent sessions...\n")

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_SESSIONS) as executor:
        futures = [executor.submit(run_single_session, u, p) for u, p in users]
        for future in as_completed(futures):
            pass

    print("\n✅ All sessions completed successfully.")

if __name__ == "__main__":
    main()
