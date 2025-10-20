---

# 🚀 Day Close Automation (Selenium + Python)

This project automates the **"Day Close"** process in the [Shakti ERP](-------------------) portal using **Python + Selenium**.
It allows you to run multiple browser sessions in parallel (concurrently) to perform automated ERP day-close actions for multiple users.

---

## 📋 Features

✅ Automates login and “Day Close” process for multiple users

✅ Supports **headless Chrome** (runs without opening browser windows)

✅ Handles optional modals automatically

✅ Runs **concurrently** using multithreading for better performance

✅ Generates detailed logs and per-user summary reports

✅ Easy configuration using simple constants at the top of the script

---

## 🧰 Technologies Used

* **Python 3.9+**
* **Selenium WebDriver**
* **Google Chrome**
* **ThreadPoolExecutor (for concurrency)**
* **Logging & CSV Reporting**

---

## 🧠 Prerequisites

Before running this project, make sure you have the following installed:

* ✅ **Python 3.9+**
  [Download Python](https://www.python.org/downloads/)
* ✅ **Google Chrome** (latest version)
  [Download Chrome](https://www.google.com/chrome/)
* ✅ **Visual Studio Code (VS Code)**
  [Download VS Code](https://code.visualstudio.com/)
* ✅ **Git** *(optional, for cloning repository)*
  [Download Git](https://git-scm.com/downloads)

---

## ⚙️ Step-by-Step Setup Guide (A → Z)

Follow these steps carefully to set up and run the project successfully in your own system.

---

### 1️⃣ Clone the repository

If you have Git installed:

```bash
git clone https://github.com/your-username/day-close-automation.git
cd day-close-automation
```

Or simply download the ZIP file from GitHub and extract it to a folder.

---

### 2️⃣ Create a Virtual Environment (venv)

Creating a virtual environment keeps all dependencies isolated for this project.

#### For Windows:

```bash
python -m venv venv
```

#### For macOS/Linux:

```bash
python3 -m venv venv
```

---

### 3️⃣ Activate the Virtual Environment

#### On Windows (Command Prompt or VS Code Terminal):

```bash
venv\Scripts\activate
```

#### On macOS/Linux:

```bash
source venv/bin/activate
```

After activation, your terminal should show `(venv)` at the beginning of the line, like:

```
(venv) PS D:\day-close-automation>
```

---

### 4️⃣ Create a `requirements.txt` File

Create a new file named **`requirements.txt`** in your project folder and add the following lines:

```txt
selenium>=4.25.0
webdriver-manager>=4.0.2
```

This ensures Selenium and WebDriver Manager are installed properly.

---

### 5️⃣ Install Required Packages

While the virtual environment is activated, run:

```bash
pip install -r requirements.txt
```

This will automatically install all required dependencies.

✅ **Installed packages:**

* `selenium` → Used for browser automation
* `webdriver-manager` → Automatically installs & manages ChromeDriver

---

### 6️⃣ Set Up ChromeDriver Automatically (No Manual Setup Needed)

Since we’re using `webdriver-manager`, ChromeDriver will automatically download and manage the correct version for your installed Chrome browser.

In the code, ensure this part is present:

```python
from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
```

No need to manually place `chromedriver.exe` in your PATH!

---

### 7️⃣ Add Your Credentials File (`creds3.csv`)

Your credentials file should be in the same directory as the script.

**Example:**

```
username,password
05158,123456
05159,123456
```

> ⚠️ If `creds3.csv` is missing, the script will automatically create a sample file for you.

---

### 8️⃣ Project Folder Structure

```
day-close-automation/
│
├── creds3.csv                # User credentials (username, password)
├── results/                  # Folder for logs and summary reports
├── Multipleselem.py          # Main automation script
├── requirements.txt          # Dependencies list
└── README.md                 # Documentation (this file)
```

---

### 9️⃣ Run the Automation Script

Make sure your virtual environment is activated in VS Code, then run:

```bash
python dayclose_loop.py
```

The script will:

1. Read credentials from `creds3.csv`
2. Open browser sessions concurrently
3. Log into ERP for each user
4. Perform the Day Close process
5. Generate logs and summary reports in the `results/` folder

---

## ⚙️ Configurable Parameters

You can customize the script by editing the following variables at the top of `dayclose_loop.py`:

| Parameter             | Description                                  | Example                                                            |
| --------------------- | -------------------------------------------- | ------------------------------------------------------------------ |
| `CSV_FILE`            | Path to your credentials file                | `"creds3.csv"`                                                     |
| `RESULTS_DIR`         | Directory where logs and summaries are saved | `"results"`                                                        |
| `URL`                 | ERP login URL                                | `...................................`                              |
| `LOOP_DURATION`       | Duration (seconds) to keep looping           | `60`                                                               |
| `CONCURRENCY`         | Number of concurrent browser sessions        | `10`                                                               |
| `DELAY_BETWEEN_LOOPS` | Delay between loop cycles (seconds)          | `0.5`                                                              |

---

## 📊 Output Files

After each run, the following files are automatically created in the `results/` folder:

### 🧾 Log File

Example:
`day_close_loop_20251018_213045.log`
Contains all activity logs, timestamps, and error messages.

### 📈 Summary File

Example:
`day_close_summary_20251018_213045.csv`
Contains per-user statistics:

| username | total_attempts | successes | failures | errors | success_rate |
| -------- | -------------- | --------- | -------- | ------ | ------------ |

---

## 🧰 Troubleshooting Guide

| Issue                    | Cause                        | Solution                                       |
| ------------------------ | ---------------------------- | ---------------------------------------------- |
| `chromedriver` not found | ChromeDriver not installed   | `webdriver-manager` handles this automatically |
| Browser not opening      | Running in headless mode     | Remove `--headless` from Chrome options        |
| Login fails              | Wrong credentials            | Check your `creds3.csv` file                   |
| Script exits immediately | No credentials found         | Ensure your CSV file is not empty              |
| ERP site not loading     | Slow internet or server down | Retry or increase wait time in script          |

---

## 🏁 Example Terminal Output

```
======================================================
CONTINUOUS DAY CLOSE LOOP AUTOMATION
======================================================
🎯 Target: ...........................
⏱️  Loop Duration: 60 seconds
🔢 Concurrency: 10
📊 Loaded 50 credentials
🚀 Starting continuous day close loop for 60 seconds...
[Loop 1] ✅ Completed: 48/50 successful
📊 Summary written to results/day_close_summary_20251018_213045.csv
🏁 Loop completed: 12 iterations in 60.01s
```

---

## 💡 Tips

* Keep concurrency (`CONCURRENCY`) moderate (5–10) for best performance.
* Use **sandbox ERP** or a test environment — avoid running this on a live system.
* Adjust sleep durations (`time.sleep`) if your ERP is slow to respond.
* Always run in a virtual environment to avoid dependency conflicts.

---

## 📜 License

This project is open-source under the **MIT License** — free to use and modify.

---

## 👨‍💻 Author

**Rakib Ahmed**
🎯 *Data Analyst | Automation Enthusiast*
📧 [Gmail](rakib429395@gmail.com)
🔗 [GitHub](https://github.com/rk-ahmed) • [LinkedIn](https://linkedin.com/in/your-profile)

---
