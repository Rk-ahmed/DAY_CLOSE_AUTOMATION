from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ---------------- CONFIG ----------------
username = '05158'
password = '123456'
url = "https://sandboxerp.shakti.org.bd:8072/Home/Login?ReturnUrl=%2F"

# ---------------- BROWSER SETUP ----------------
options = Options()
options.add_argument("--incognito")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)  # Increased wait for reliability

driver.get(url)

# ---------------- LOGIN ----------------
wait.until(EC.presence_of_element_located((By.ID, "emailaddress"))).send_keys(username)
wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)

# Click login button using working XPath
login_button = wait.until(
    EC.element_to_be_clickable((By.XPATH, "/html/body/section/div[2]/div/div/div/form/div[5]/button"))
)
login_button.click()

# ---------------- HANDLE OPTIONAL MODAL ----------------
try:
    modal_button = WebDriverWait(driver, 3).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="responseModal"]/div/div/div[3]/button'))
    )
    modal_button.click()
except:
    pass  # Continue if modal doesn't appear

# ---------------- NAVIGATE TO DAY CLOSE ----------------
# Click MIS
wait.until(EC.element_to_be_clickable(
    (By.XPATH, '//*[@id="homePage"]/div[1]/div/div[1]/div[7]/a/div'))
).click()

# Wait for Day Open/Close menu container to ensure it’s loaded
wait.until(EC.visibility_of_element_located(
    (By.XPATH, '/html/body/div[1]/div[3]/div[1]/div/div/div/div[2]/div/div[2]/div/ul')
))

# Click Day Open/Close
day_open_close_btn = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, '/html/body/div[1]/div[3]/div[1]/div/div/div/div[2]/div/div[2]/div/ul/li[1]/a')
    )
)
day_open_close_btn.click()

# Click Day Close button
day_close_btn = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, '/html/body/div[1]/div[3]/div[1]/div[1]/div/div/div[3]/div/button')
    )
)
day_close_btn.click()

# Click Yes to confirm Day Close
yes_button = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, '/html/body/div[1]/div[3]/div[1]/div[5]/div/div/div[3]/button[2]')
    )
)
yes_button.click()

print("✅ Day Close completed successfully!")
driver.quit()
