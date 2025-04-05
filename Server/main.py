from flask import Flask
from pocketbase import Pocketbase

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import os
import signal
import threading



def create_app():
    
    app = Flask(__name__)
    
    @app.route("/")
    def default():
        return 1
    

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File to store proxy list
PROXY_FILE = "proxylist.txt"

# Global flag to control execution
running = True

# User agent pool for rotation
USER_AGENTS = [
    # Chrome on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',  # Windows 7
    
    # Chrome on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',

    # Chrome on Linux
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',

    # Firefox on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',  # Windows 8.1

    # Firefox on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6; rv:125.0) Gecko/20100101 Firefox/125.0',

    # Firefox on Linux
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0',

    # Safari on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',

    # Edge on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.2420.65',
    'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.2478.51',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.2535.51',

    # Opera on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/108.0.0.0',
    'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/109.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 OPR/110.0.0.0',

    # Opera on Linux
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/108.0.0.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/109.0.0.0',
]




def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully exit the script"""
    global running
    logger.info("Stopping script (this may take a moment to complete current view)...")
    running = False

# Register the signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)



# Unchanged functions: fetch_proxies, get_random_proxy, try_open_comments, simulate_short_view
def fetch_proxies():
    """Fetch free proxies from multiple sources and save to a file"""
    logger.info("Fetching fresh proxies...")
    proxies = []
    sources = [
        "https://www.sslproxies.org/",
        "https://free-proxy-list.net/",
        "https://www.us-proxy.org/",
        "https://www.proxynova.com/proxy-server-list/country-us/",
        "https://www.proxynova.com/proxy-server-list/country-ca/"
    ]
    
    for source in sources:
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            logger.info(f"Fetching proxies from {source} with UA: {headers['User-Agent']}")
            response = requests.get(source, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if "proxynova" in source:
                table = soup.find('table', {'id': 'tbl_proxy_list'})
                if not table:
                    logger.warning(f"No proxy table found in {source}")
                    continue
                for row in table.find('tbody').find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 3:  # IP, port, protocol
                        ip = cells[0].text.strip()
                        port = cells[1].text.strip()
                        protocol = cells[2].text.strip().lower()
                        if "https" in protocol or "http" in protocol:
                            proxy = f"{ip}:{port}"
                            proxies.append(proxy)
            else:
                table = soup.find('table', {'class': 'table table-striped table-bordered'})
                if not table:
                    logger.warning(f"No proxy table found in {source}")
                    continue
                for row in table.tbody.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        ip = cells[0].text.strip()
                        port = cells[1].text.strip()
                        https = cells[6].text.strip()
                        if https.lower() == 'yes':
                            proxy = f"{ip}:{port}"
                            proxies.append(proxy)
        except Exception as e:
            logger.error(f"Error fetching proxies from {source}: {str(e)}")
    
    working_proxies = []
    logger.info(f"Testing {len(proxies)} proxies for viability...")
    
    def test_proxy(proxy):
        try:
            test_url = "https://www.google.com"
            proxies_dict = {
                "http": f"http://{proxy}",
                "https": f"https://{proxy}"
            }
            response = requests.get(test_url, proxies=proxies_dict, timeout=5)
            if response.status_code == 200:
                return proxy
        except:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(test_proxy, proxies))
    
    working_proxies = [proxy for proxy in results if proxy]
    with open(PROXY_FILE, "w") as f:
        for proxy in working_proxies:
            f.write(f"{proxy}\n")
    
    logger.info(f"Saved {len(working_proxies)} working proxies to {PROXY_FILE}")
    return working_proxies

def get_random_proxy():
    """Get a random proxy from the proxy file or fetch new ones if needed"""
    proxies = []
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
    if not proxies:
        proxies = fetch_proxies()
    if not proxies:
        logger.warning("No proxies available")
        return None
    proxy = random.choice(proxies)
    logger.info(f"Using proxy: {proxy}")
    return proxy

def try_open_comments(driver):
    """Attempt to open the comments section using multiple methods"""
    logger.info("Attempting to open comments section")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    
    methods = [
        (By.XPATH, "//button[@aria-label='Show comments']"),
        (By.CSS_SELECTOR, "ytm-comment-section-renderer"),
        (By.XPATH, "//*[contains(text(), 'Comments')]"),
        (By.CSS_SELECTOR, "button[aria-label='Comments']"),
        (By.ID, "comments-button"),
        (By.CSS_SELECTOR, ".yt-spec-touch-feedback-shape__fill")
    ]
    
    for by, selector in methods:
        try:
            element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((by, selector)))
            if selector == ".yt-spec-touch-feedback-shape__fill":
                button = element.find_element(By.XPATH, "./ancestor::button[contains(@aria-label, 'Comments')]")
            else:
                button = element
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable(button))
            actions = ActionChains(driver)
            actions.move_to_element(button).click().perform()
            logger.info(f"Opened comments using {by}: {selector}")
            return True
        except TimeoutException:
            logger.warning(f"Could not find comments element with {by}: {selector}")
        except ElementClickInterceptedException:
            logger.warning(f"Click intercepted for {by}: {selector}, trying JavaScript click")
            try:
                driver.execute_script("arguments[0].click();", button)
                logger.info(f"Opened comments using JavaScript click on {by}: {selector}")
                return True
            except:
                logger.warning(f"JavaScript click failed for {by}: {selector}")
        except Exception as e:
            logger.warning(f"Error with {by}: {selector} - {str(e)}")
    
    try:
        driver.execute_script("""
            const comments = document.querySelector('ytm-comment-section-renderer, #comments-button, button[aria-label="Comments"], .yt-spec-touch-feedback-shape__fill');
            if (comments) {
                const button = comments.closest('button[aria-label*="Comments"]') || comments;
                button.click();
            }
        """)
        if driver.execute_script("return !!document.querySelector('ytm-comment-section-renderer.visible');"):
            logger.info("Opened comments section via JavaScript")
            return True
        else:
            logger.warning("Could not confirm comments section opened")
    except:
        logger.warning("JavaScript method failed to open comments")
    return False

def simulate_short_view(short_url, proxy=None):
    chrome_options = Options()
    chrome_options.add_argument("--headless=True")
    chrome_options.add_argument("--window-size=412,732")
    ua = random.choice(USER_AGENTS)
    chrome_options.add_argument(f"--user-agent={ua}")
    chrome_options.add_argument("--mute-audio")
    logger.info(f"Using user agent: {ua}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    if proxy:
        chrome_options.add_argument(f"--proxy-server={proxy}")
        logger.info(f"Setting up Chrome with proxy: {proxy}")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """
    })
    
    try:
        logger.info("Opening YouTube homepage")
        driver.get("https://www.youtube.com")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "ytd-app")))
        logger.info("YouTube homepage loaded successfully")
        time.sleep(3)
        
        short_id = short_url.split("/")[-1]
        logger.info(f"Extracted Short ID: {short_id}")
        
        try:
            search_bar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "search_query"))
            )
            search_bar.click()
            search_bar.send_keys(f"youtube shorts {short_id}")
            search_button = driver.find_element(By.ID, "search-icon-legacy")
            search_button.click()
            logger.info(f"Searched for Short ID: {short_id}")
            time.sleep(3)
            
            short_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '/shorts/{short_id}')]"))
            )
            short_link.click()
            logger.info("Clicked on the Short video")
            time.sleep(5)
        except TimeoutException:
            logger.error("Could not find the Short via search, falling back to direct URL")
            driver.get(short_url)
            time.sleep(5)
        
        driver.execute_script("""
            const dialogs = document.querySelectorAll('tp-yt-paper-dialog, ytd-popup-container');
            dialogs.forEach(dialog => dialog.remove());
            const overlays = document.querySelectorAll('.ytd-consent-bump-v2-lightbox');
            overlays.forEach(overlay => overlay.remove());
            const fixedElements = document.querySelectorAll('.ytd-popup-container, .ytd-mealbar-promo-renderer');
            fixedElements.forEach(el => el.remove());
        """)
        logger.info("Attempted to remove popups via JavaScript")
        time.sleep(2)
        
        logger.info("Attempting to find and interact with the video player...")
        try:
            video = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "video")))
            logger.info("Video element found!")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", video)
            time.sleep(1)
            try:
                actions = ActionChains(driver)
                actions.move_to_element(video).click().perform()
            except ElementClickInterceptedException:
                logger.warning("Click intercepted, using JavaScript to play video")
                driver.execute_script("arguments[0].play();", video)
        except TimeoutException:
            logger.warning("Could not find video with specific selector, trying a direct approach")
            videos = driver.find_elements(By.TAG_NAME, "video")
            if videos:
                logger.info(f"Found {len(videos)} video elements with tag search")
                video = videos[0]
                driver.execute_script("arguments[0].play();", video)
            else:
                logger.error("No video elements found on the page")
                driver.save_screenshot("no_video.png")
                return False
        
        time.sleep(3)
        is_playing = driver.execute_script("""
            const videos = document.querySelectorAll('video');
            for (let i = 0; i < videos.length; i++) {
                if (!videos[i].paused) return true;
            }
            return false;
        """)
        if is_playing:
            logger.info("Video is playing successfully!")
        else:
            logger.warning("Video not playing, attempting to resume")
            driver.execute_script("""
                const videos = document.querySelectorAll('video');
                videos.forEach(v => v.play());
            """)
            time.sleep(2)
        
        watch_time = random.uniform(60, 120)
        logger.info(f"Watching for {watch_time:.1f} seconds")
        start_time = time.time()
        comments_opened = False
        attempt_times = sorted([random.uniform(0, watch_time) for _ in range(3)])
        
        while time.time() - start_time < watch_time:
            with running.get_lock():
                if not running.value:
                    logger.info("Stopping current view early due to shutdown signal")
                    break
            elapsed = time.time() - start_time
            
            if not comments_opened and attempt_times and elapsed >= attempt_times[0]:
                if try_open_comments(driver):
                    comments_opened = True
                attempt_times.pop(0)
            
            is_playing = driver.execute_script("""
                const videos = document.querySelectorAll('video');
                for (let i = 0; i < videos.length; i++) {
                    if (!videos[i].paused) return true;
                }
                return false;
            """)
            if not is_playing:
                logger.warning("Video paused, attempting to resume")
                driver.execute_script("""
                    const videos = document.querySelectorAll('video');
                    videos.forEach(v => v.play());
                """)
            
            if random.random() < 0.2:
                small_scroll = random.randint(-10, 10)
                driver.execute_script(f"window.scrollBy(0, {small_scroll});")
            time.sleep(3)
        
        if not comments_opened:
            logger.info("Making a final attempt to open comments")
            try_open_comments(driver)
        
        logger.info("Successfully watched short!")
        return True
    except Exception as e:
        logger.error(f"Failed: {str(e)}")
        try:
            driver.save_screenshot("error.png")
            logger.info("Screenshot saved as 'error.png'")
        except:
            pass
        return False
    finally:
        driver.quit()

def thread_short_worker(urls, use_proxies, stats):
    """Worker function for each thread"""
    thread_id = threading.current_thread().name
    while running:
        shuffled_urls = urls.copy()
        random.shuffle(shuffled_urls)
        for url in shuffled_urls:
            if not running:
                break
            
            with stats["lock"]:
                stats["view_count"] += 1
                current_view = stats["view_count"]
            
            proxy = get_random_proxy() if use_proxies else None
            if use_proxies and proxy is None:
                logger.warning("No proxies available, fetching new ones...")
                fetch_proxies()
                proxy = get_random_proxy()
            
            logger.info(f"Thread {thread_id} - View attempt #{current_view} - URL: {url}")
            success = simulate_short_view(url, proxy)
            
            with stats["lock"]:
                if success:
                    stats["success_count"] += 1
                else:
                    stats["fail_count"] += 1
                
                if current_view % 10 == 0:
                    success_rate = (stats["success_count"] / current_view) * 100
                    logger.info(f"Stats: {stats['success_count']} successes, {stats['fail_count']} failures - {success_rate:.1f}% success rate")
            
            if running:
                delay = random.uniform(5, 15)
                logger.info(f"Thread {thread_id} waiting {delay:.2f} seconds before next video...")
                sleep_start = time.time()
                while running and (time.time() - sleep_start < delay):
                    time.sleep(1)

def process_shorts_continuously(urls, use_proxies=True, num_threads=3):
    """
    Process shorts continuously in random order until stopped, using multiple threads
    """
    # Shared stats dictionary with a lock for thread-safe updates
    stats = {
        "view_count": 0,
        "success_count": 0,
        "fail_count": 0,
        "lock": threading.Lock()
    }
    
    logger.info(f"Starting continuous viewing mode with {num_threads} threads. Press Ctrl+C to stop.")
    logger.info(f"Starting continuous viewing of {len(urls)} shorts in random order")
    
    if use_proxies and not os.path.exists(PROXY_FILE):
        fetch_proxies()
    
    # Start threads
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=thread_short_worker, args=(urls, use_proxies, stats))
        t.start()
        threads.append(t)
    
    # Keep main thread alive and wait for threads to finish
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        global running
        logger.info("Stopping threads due to interrupt...")
        running = False
        for t in threads:
            t.join()
    
    # Final stats
    logger.info("===== FINAL VIEWING RESULTS =====")
    logger.info(f"Total view attempts: {stats['view_count']}")
    logger.info(f"Successful views: {stats['success_count']}")
    logger.info(f"Failed views: {stats['fail_count']}")
    if stats['view_count'] > 0:
        success_rate = (stats['success_count'] / stats['view_count']) * 100
        logger.info(f"Success rate: {success_rate:.1f}%")
        
        
        
if __name__ == "__main__":
    # Variable to change the number of processes
    NUM_THREADS = 3 # Change this value to adjust the number of concurrent processes
    
    shorts_to_view = [
        "https://youtube.com/shorts/JfodRXOmAxU",
        "https://youtube.com/shorts/z2MJe0Q_A-o",
        "https://youtube.com/shorts/0CSpNp1X144",
        "https://youtube.com/shorts/s0Ui36XEbMM",
        "https://www.youtube.com/shorts/lOVVGfSKCv4",
        "https://www.youtube.com/shorts/OPSV7kjrnw8",
        "https://www.youtube.com/shorts/EuqmysuhS30",
        "https://www.youtube.com/shorts/BrsWRRqOGNk",
        "https://www.youtube.com/shorts/-yw5boY3eB4",
        "https://www.youtube.com/shorts/GaFQx3_bx7k",
        "https://www.youtube.com/shorts/F-OOCA9pxP0",
        "https://www.youtube.com/shorts/QUSrYy0Ls-w"
    ]
    
    try:
        process_shorts_continuously(shorts_to_view, use_proxies=True, num_threads=NUM_THREADS)
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        logger.info("Script execution completed")