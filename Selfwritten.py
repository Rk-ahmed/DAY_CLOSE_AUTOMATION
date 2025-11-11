import time
import tempfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

#------------- Create Chrome options-----------
options = Options()
options.add_argument("--incognito")  # For avoiding google chrome password save popup
options.add_argument("--start-maximized")  # Start maximized
# Launch browser in incognito mode
driver = webdriver.Chrome(options=options)

# ---------------- CONFIG ---------------
driver.get("https://sandboxerp.shakti.org.bd:8072/Home/Login?ReturnUrl=%2F")
time.sleep(3)

username = '08341'
password =  '123456'
# ---------------- LOGIN ----------------
#Username send
usernameid = driver.find_element(By.ID,"emailaddress")
usernameid.clear()
usernameid.send_keys(username)

#password send
passwordid = driver.find_element(By.ID, "password")
passwordid.clear()
passwordid.send_keys(password)

time.sleep(2)

#Click Login Button
login_button = driver.find_element(By.XPATH, "/html/body/section/div[2]/div/div/div/form/div[5]/button")
login_button.click()
time.sleep(2)

#Wait for modal button and clickable
wait = WebDriverWait(driver, 5)
modal_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="responseModal"]/div/div/div[3]/button')))
modal_button.click()
time.sleep(2)

#Click on MIS 
mis_button = driver.find_element(By.XPATH, '//*[@id="homePage"]/div[1]/div/div[1]/div[7]/a/div')
mis_button.click()
time.sleep(2)

#Click Day Open or Close
Day_open_or_close_button = driver.find_element(By.XPATH, '/html/body/div[1]/div[3]/div[1]/div/div/div/div[2]/div/div[2]/div/ul/li[1]/a')
Day_open_or_close_button.click()
time.sleep(5)

#Click Day Close
Day_Close = driver.find_element(By.XPATH, '/html/body/div[1]/div[3]/div[1]/div[1]/div/div/div[3]/div/button')
Day_Close.click()
time.sleep(5)

#Wait for modal button and Yes clickable
wait = WebDriverWait(driver, 3)
yes_button = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[3]/div[1]/div[5]/div/div/div[3]/button[2]')))
yes_button.click()
time.sleep(5)

#confirmed the Day Close
wait = webdriver(driver, 5*60)
succes_button = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[3]/div[2]/div/div/div[3]/button')))
succes_button.click()
time.sleep(1)
