from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import csv
import asyncio
import time
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

# ============ CONFIGURABLE PARAMETERS ============
CSV_FILE = "creds3.csv"  # CSV format: username,password
RESULTS_DIR = "results"
URL = "https://sandboxerp.shakti.org.bd:8072/Home/Login?ReturnUrl=%2F"

LOOP_DURATION = 60  # Total duration in seconds to keep looping (60 Seconds)
CONCURRENCY = 10  # Number of concurrent browser sessions
DELAY_BETWEEN_LOOPS = 0.5  # Delay between each complete loop cycle

# ---------------- LOGGING ----------------
def setup_logging():
    """Configure logging with file and console output."""
    log_dir = Path(RESULTS_DIR)
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"day_close_loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ---------------- UTILS ----------------
def load_credentials(csv_file):
    """Load credentials from CSV file."""
    credentials = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for i, row in enumerate(reader):
                username = (row.get("username") or row.get("user") or 
                           row.get("id") or row.get("email"))
                password = (row.get("password") or row.get("pass") or 
                           row.get("pwd"))
                if username and password:
                    credentials.append({
                        'username': username.strip(),
                        'password': password.strip()
                    })
                else:
                    logger.warning(f"Row {i+1} missing username or password")
        logger.info(f"✅ Loaded {len(credentials)} credentials from {csv_file}")
        return credentials
    except FileNotFoundError:
        logger.error(f"❌ CSV file not found: {csv_file}")
        logger.info("Creating sample CSV file...")
        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'password'])
            writer.writerow(['05158', '123456'])
            writer.writerow(['05159', '123456'])
        logger.info(f"✅ Sample {csv_file} created. Please edit with your credentials.")
        return []
    except Exception as e:
        logger.error(f"❌ Error reading CSV: {e}")
        return []

def write_summary(all_results, elapsed, loop_count):
    """Write summary statistics to CSV."""
    Path(RESULTS_DIR).mkdir(exist_ok=True)
    summary_file = f"{RESULTS_DIR}/day_close_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Aggregate results by username
    user_stats = {}
    for result in all_results:
        username = result['username']
        if username not in user_stats:
            user_stats[username] = {
                'username': username,
                'total_attempts': 0,
                'successes': 0,
                'failures': 0,
                'errors': 0
            }
        user_stats[username]['total_attempts'] += 1
        if result['status'] == 'success':
            user_stats[username]['successes'] += 1
        elif result['status'] == 'failure':
            user_stats[username]['failures'] += 1
        else:
            user_stats[username]['errors'] += 1
    
    # Write summary
    fieldnames = ['username', 'total_attempts', 'successes', 'failures', 'errors', 'success_rate']
    try:
        with open(summary_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for stats in user_stats.values():
                stats['success_rate'] = f"{stats['successes']/stats['total_attempts']*100:.1f}%"
                writer.writerow(stats)
        logger.info(f"📊 Summary written to {summary_file}")
    except Exception as e:
        logger.error(f"❌ Error writing summary: {e}")
    
    return summary_file

# ---------------- DAY CLOSE PROCESS ----------------
def process_day_close(username, password, loop_num, attempt_num, semaphore):
    """Process day close for a single credential."""
    with semaphore:  # Control concurrency
        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            logger.info(f"[Loop {loop_num}] Attempt {attempt_num} | Starting for user: {username}")
            
            # Setup headless browser
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--incognito")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--log-level=3")  # Suppress browser logs
            
            driver = webdriver.Chrome(options=options)
            wait = WebDriverWait(driver, 20)
            
            driver.get(URL)
            
            # ---------------- LOGIN ----------------
            wait.until(EC.presence_of_element_located((By.ID, "emailaddress"))).send_keys(username)
            wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)
            
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
                pass
            
            # ---------------- NAVIGATE TO DAY CLOSE ----------------
            # Click MIS
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="homePage"]/div[1]/div/div[1]/div[7]/a/div'))
            ).click()
            
            # Wait for Day Open/Close menu container
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
            
            # Click Yes to confirm Day Close (WAIT UNTIL THIS COMPLETES)
            yes_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '/html/body/div[1]/div[3]/div[1]/div[5]/div/div/div[3]/button[2]')
                )
            )
            yes_button.click()
            
            # Wait for operation to complete
            time.sleep(3)
            
            logger.info(f"[Loop {loop_num}] ✅ Attempt {attempt_num} | User {username}: SUCCESS")
            
            driver.quit()
            
            return {
                "loop": loop_num,
                "attempt": attempt_num,
                "username": username,
                "status": "success",
                "timestamp": timestamp,
                "message": "Day close completed"
            }
            
        except Exception as e:
            logger.error(f"[Loop {loop_num}] ❌ Attempt {attempt_num} | User {username}: ERROR - {str(e)}")
            try:
                driver.quit()
            except:
                pass
            
            return {
                "loop": loop_num,
                "attempt": attempt_num,
                "username": username,
                "status": "error",
                "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "message": str(e)
            }

# ---------------- BATCH EXECUTION ----------------
def run_single_batch(creds, loop_num, semaphore):
    """Run one complete batch of all credentials concurrently."""
    results = []
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [
            executor.submit(process_day_close, cred['username'], cred['password'], loop_num, i, semaphore)
            for i, cred in enumerate(creds, 1)
        ]
        
        for future in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Thread exception: {e}")
                results.append({
                    "loop": loop_num,
                    "attempt": 0,
                    "username": "unknown",
                    "status": "error",
                    "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    "message": str(e)
                })
    
    return results

# ---------------- CONTINUOUS LOOP ----------------
def continuous_loop(creds, duration):
    """Continuously loop through credentials for specified duration."""
    start_time = time.time()
    end_time = start_time + duration
    all_results = []
    loop_count = 0
    
    # Semaphore to control concurrency
    semaphore = threading.Semaphore(CONCURRENCY)
    
    logger.info(f"🚀 Starting continuous day close loop for {duration} seconds...")
    logger.info(f"📋 Credentials: {len(creds)}, Concurrency: {CONCURRENCY}")
    logger.info("=" * 70)
    
    while time.time() < end_time:
        loop_count += 1
        remaining = end_time - time.time()
        
        if remaining <= 0:
            break
        
        logger.info(f"[Loop {loop_count}] 🔄 Starting batch (Time remaining: {remaining:.1f}s)...")
        
        # Run one complete batch
        batch_results = run_single_batch(creds, loop_count, semaphore)
        all_results.extend(batch_results)
        
        # Count successes in this batch
        batch_successes = sum(1 for r in batch_results if r['status'] == 'success')
        logger.info(f"[Loop {loop_count}] ✅ Completed: {batch_successes}/{len(creds)} successful")
        
        # Small delay before next loop (if time permits)
        remaining = end_time - time.time()
        if remaining > DELAY_BETWEEN_LOOPS:
            time.sleep(DELAY_BETWEEN_LOOPS)
    
    total_elapsed = time.time() - start_time
    
    logger.info("=" * 70)
    logger.info(f"🏁 Loop completed: {loop_count} iterations in {total_elapsed:.2f}s")
    
    return all_results, total_elapsed, loop_count

# ---------------- MAIN ----------------
def main():
    logger.info("=" * 70)
    logger.info("CONTINUOUS DAY CLOSE LOOP AUTOMATION")
    logger.info("=" * 70)
    logger.info(f"🎯 Target: {URL}")
    logger.info(f"⏱️  Loop Duration: {LOOP_DURATION} seconds")
    logger.info(f"🔢 Concurrency: {CONCURRENCY}")
    logger.info(f"⏳ Delay Between Loops: {DELAY_BETWEEN_LOOPS}s")
    logger.info("=" * 70)
    
    creds = load_credentials(CSV_FILE)
    if not creds:
        logger.error(f"❌ No valid credentials found in {CSV_FILE}")
        return
    
    logger.info(f"📊 Loaded {len(creds)} credential pairs")
    estimated_loops = int(LOOP_DURATION / (len(creds) * 5 + DELAY_BETWEEN_LOOPS))  # ~5s per operation
    logger.info(f"📈 Estimated loops: ~{estimated_loops}")
    logger.info(f"📌 Estimated total attempts: ~{estimated_loops * len(creds)}")
    logger.info("=" * 70)
    
    try:
        all_results, elapsed, loop_count = continuous_loop(creds, LOOP_DURATION)
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Test interrupted by user")
        return
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        return
    
    # Calculate statistics
    total_attempts = len(all_results)
    successes = [r for r in all_results if r['status'] == 'success']
    failures = [r for r in all_results if r['status'] == 'failure']
    errors = [r for r in all_results if r['status'] == 'error']
    
    logger.info("=" * 70)
    logger.info("📊 FINAL RESULTS")
    logger.info("=" * 70)
    logger.info(f"⏱️  Duration: {elapsed:.2f}s")
    logger.info(f"🔁 Total Loops: {loop_count}")
    logger.info(f"📝 Total Attempts: {total_attempts}")
    logger.info(f"⚡ Rate: {total_attempts/elapsed:.2f} attempts/second")
    logger.info("")
    logger.info(f"✅ Successes: {len(successes)} ({len(successes)/total_attempts*100:.1f}%)")
    logger.info(f"❌ Failures: {len(failures)} ({len(failures)/total_attempts*100:.1f}%)")
    logger.info(f"⚠️  Errors: {len(errors)} ({len(errors)/total_attempts*100:.1f}%)")
    
    # Write detailed summary
    summary_file = write_summary(all_results, elapsed, loop_count)
    
    # Write detailed results
    ''' detailed_file = f"{RESULTS_DIR}/day_close_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        with open(detailed_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['loop', 'attempt', 'username', 'status', 'timestamp', 'message']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        logger.info(f"📄 Detailed results: {detailed_file}")
    except Exception as e:
        logger.error(f"❌ Error writing detailed results: {e}")
    
    logger.info("=" * 70)
    logger.info("📊 Check the summary file for per-user statistics")
    logger.info("=" * 70)'''

if __name__ == "__main__":
    main()