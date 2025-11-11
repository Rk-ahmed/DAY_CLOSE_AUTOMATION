import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---------------- CONFIG ----------------
URL = "https://sandboxerp.shakti.org.bd:8072/Home/Login?ReturnUrl=%2F"
CSV_FILE = "creds3.csv"
WAIT_TIME = 8
SHORT_WAIT = 2
INITIAL_POPUP_WAIT = 5
MAX_CONCURRENT_SESSIONS = 5   # <-- how many browsers to run in parallel

# ---------------- DRIVER (Headless Only) ----------------
def create_headless_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")       # use new headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    return driver

# ---------------- LOGIN FLOW ----------------
def run_single_session(username, password):
    start_time = time.time()
    print(f"[{username}] → Starting session")
    driver = create_headless_driver()
    driver.get(URL)

    try:
        wait = WebDriverWait(driver, WAIT_TIME)

        # login
        username_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="emailaddress"]')))
        username_field.clear()
        username_field.send_keys(username)
        password_field = driver.find_element(By.XPATH, '//*[@id="password"]')
        password_field.clear()
        password_field.send_keys(password)
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/section/div[2]/div/div/div/form/div[5]/button')))
        driver.execute_script("arguments[0].click();", login_btn)

        # wait for homepage
        try:
            WebDriverWait(driver, INITIAL_POPUP_WAIT).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="homePage"]/div[1]/div/div[1]/div[7]/a/div/div/p'))
            )
            print(f"[{username}] Logged in successfully")
        except TimeoutException:
            print(f"[{username}] Homepage not detected but continuing")

        # navigate to MIS → Day Information
        mis_menu = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="homePage"]/div[1]/div/div[1]/div[7]/a/div/div/p')))
        driver.execute_script("arguments[0].click();", mis_menu)
        day_info = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="02"]/div[2]/div/div[2]/div/ul/li[1]/a')))
        driver.execute_script("arguments[0].click();", day_info)

       # try to click Day Open / Close
        try:
            open_btn = driver.find_element(By.XPATH, '//*[@id="day-information"]/div[1]/div/div/div[3]/div/button')
            driver.execute_script("arguments[0].click();", open_btn)
            print(f"[{username}] Clicked Day Open")
        except NoSuchElementException:
            try:
                close_btn = driver.find_element(By.XPATH, '//*[@id="day-information"]/div[1]/div/div/div[3]/div/button[2]')
                driver.execute_script("arguments[0].click();", close_btn)
                print(f"[{username}] Clicked Day Close")
            except NoSuchElementException:
                print(f"[{username}] No Day Open/Close button found")

        time.sleep(0.5)
        print(f"[{username}] ✓ Session completed in {time.time()-start_time:.2f}s")

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
            pass  # just wait for all to finish

    print("\n✅ Load test completed.")

if __name__ == "__main__":
    main()