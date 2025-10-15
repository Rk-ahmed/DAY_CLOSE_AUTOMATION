import pyautogui
import time
import json

# ================= CONFIGURATION =================
URL = "https://sandboxerp.shakti.org.bd:8072/Home/Login?ReturnUrl=%2F"
USERNAME = "08341"
PASSWORD = "123456"
WAIT_TIME = 3  # seconds between actions for safer clicking

# ================= COORDINATES =================
coords = {
    "username": {"x": 984, "y": 916},
    "password": {"x": 984, "y": 918},
    "warning": {"x": 985, "y": 957},
    "login": {"x": 965, "y": 712},
    "MIS": {"x": 221, "y": 511},
    "day_info": {"x": 763, "y": 295},
    "day_action": {"x": 353, "y": 331},
    "yes": {"x": 1071, "y": 663}
}

# ================= FUNCTIONS =================
def open_browser():
    print("Opening Chrome browser...")
    pyautogui.hotkey('win', 'r')
    time.sleep(1)
    pyautogui.write('chrome')
    pyautogui.press('enter')
    time.sleep(3)
    pyautogui.write(URL)
    pyautogui.press('enter')
    time.sleep(3)  # wait for page to load completely

def login():
    print("Logging in...")
    # Username
    pyautogui.click(coords["username"]["x"], coords["username"]["y"])
    pyautogui.write(USERNAME)
    time.sleep(WAIT_TIME)

    # Password
    pyautogui.click(coords["password"]["x"], coords["password"]["y"])
    pyautogui.write(PASSWORD)
    time.sleep(WAIT_TIME)

    # Login button
    pyautogui.click(coords["login"]["x"], coords["login"]["y"])
    time.sleep(3)  # wait for dashboard to load

def open_mis_and_day_info():
    print("Navigating to Day Information...")
    # Click MIS
    pyautogui.click(coords["MIS"]["x"], coords["MIS"]["y"])
    time.sleep(WAIT_TIME)

    # Click Day Information
    pyautogui.click(coords["day_info"]["x"], coords["day_info"]["y"])
    time.sleep(3)

def perform_day_action(action="Open"):
    print(f"Performing Day {action}...")
    # Click Day Action Dropdown
    pyautogui.click(coords["day_action"]["x"], coords["day_action"]["y"])
    time.sleep(3)

    # Type Day Open or Day Close
    pyautogui.write(f"Day {action}")
    pyautogui.press('enter')
    time.sleep(3)

    # Confirm YES
    pyautogui.click(coords["yes"]["x"], coords["yes"]["y"])
    time.sleep(2)

    print(f"Day {action} completed successfully!")

def main():
    action = input("Enter action (Open/Close): ").strip().capitalize()
    if action not in ["Open", "Close"]:
        print("Invalid action. Please type 'Open' or 'Close'.")
        return

    open_browser()
    login()
    open_mis_and_day_info()
    perform_day_action(action)

    print("Automation finished successfully. Closing browser...")
    time.sleep(60)
    pyautogui.hotkey('alt', 'f4')
    print("Browser closed.")

# ================= MAIN EXECUTION =================
if __name__ == "__main__":
    main()
