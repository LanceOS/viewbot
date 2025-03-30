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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File to store proxy list
PROXY_FILE = "proxylist.txt"

# Global flag to control execution
running = True

# User agent pool for rotation
USER_AGENTS = [
    # Desktop
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    # Mobile
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1'
]

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully exit the script"""
    global running
    logger.info("Stopping script (this may take a moment to complete current view)...")
    running = False

# Register the signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

def fetch_proxies():
    """
    Fetch free proxies from multiple sources and save to a file
    """
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
    """
    Get a random proxy from the proxy file or fetch new ones if needed
    """
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
    """
    Attempt to open the comments section using multiple methods
    """
    logger.info("Attempting to open comments section")
    # Scroll to the bottom to load comments if needed
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
            # For yt-spec-touch-feedback-shape__fill, we need to find the parent button
            if selector == ".yt-spec-touch-feedback-shape__fill":
                button = element.find_element(By.XPATH, "./ancestor::button[contains(@aria-label, 'Comments')]")
            else:
                button = element
            # Ensure the button is clickable
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
    
    # If all methods fail, try JavaScript to find and click
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
    chrome_options.add_argument("--window-size=412,732")
    ua = random.choice(USER_AGENTS)  # Random user agent per view
    chrome_options.add_argument(f"--user-agent={ua}")
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
        # Start at the YouTube homepage
        logger.info("Opening YouTube homepage")
        driver.get("https://www.youtube.com")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "ytd-app")))
        logger.info("YouTube homepage loaded successfully")
        time.sleep(3)
        
        # Extract the Short ID from the URL
        short_id = short_url.split("/")[-1]
        logger.info(f"Extracted Short ID: {short_id}")
        
        # Search for the specific Short
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
            
            # Click on the first Shorts result
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
        
        # Remove popups
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
        
        # Find and play the video
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
        
        # Set watch time between 1 and 2 minutes (60-120 seconds)
        watch_time = random.uniform(60, 120)
        logger.info(f"Watching for {watch_time:.1f} seconds")
        start_time = time.time()
        comments_opened = False  # Flag to ensure comments are opened at least once
        # Generate 3 random attempt times for opening comments
        attempt_times = sorted([random.uniform(0, watch_time) for _ in range(3)])
        
        while time.time() - start_time < watch_time:
            if not running:
                logger.info("Stopping current view early due to shutdown signal")
                break
            elapsed = time.time() - start_time
            
            # Attempt to open comments at predefined random times (max 3 attempts)
            if not comments_opened and attempt_times and elapsed >= attempt_times[0]:
                if try_open_comments(driver):
                    comments_opened = True
                attempt_times.pop(0)
            
            # Check if video is still playing
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
            
            # Small random scroll to simulate engagement
            if random.random() < 0.2:
                small_scroll = random.randint(-10, 10)
                driver.execute_script(f"window.scrollBy(0, {small_scroll});")
            time.sleep(3)
        
        # Final attempt to open comments if not opened yet
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

def process_shorts_continuously(urls, use_proxies=True):
    """
    Process shorts continuously in random order until stopped
    """
    global running
    view_count = 0
    success_count = 0
    fail_count = 0
    
    logger.info("Starting continuous viewing mode. Press Ctrl+C to stop.")
    logger.info(f"Starting continuous viewing of {len(urls)} shorts in random order")
    
    if use_proxies and not os.path.exists(PROXY_FILE):
        fetch_proxies()
    
    while running:
        shuffled_urls = urls.copy()
        random.shuffle(shuffled_urls)
        for url in shuffled_urls:
            if not running:
                break
            view_count += 1
            proxy = get_random_proxy() if use_proxies else None
            if use_proxies and proxy is None:
                logger.warning("No proxies available, fetching new ones...")
                fetch_proxies()
                proxy = get_random_proxy()
            
            logger.info(f"View attempt #{view_count} - URL: {url}")
            success = simulate_short_view(url, proxy)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            if view_count % 10 == 0:
                success_rate = (success_count / view_count) * 100
                logger.info(f"Stats: {success_count} successes, {fail_count} failures - {success_rate:.1f}% success rate")
            
            if running:
                delay = random.uniform(5, 15)
                logger.info(f"Waiting {delay:.2f} seconds before next video...")
                sleep_start = time.time()
                while running and (time.time() - sleep_start < delay):
                    time.sleep(1)
    
    logger.info("===== FINAL VIEWING RESULTS =====")
    logger.info(f"Total view attempts: {view_count}")
    logger.info(f"Successful views: {success_count}")
    logger.info(f"Failed views: {fail_count}")
    if view_count > 0:
        success_rate = (success_count / view_count) * 100
        logger.info(f"Success rate: {success_rate:.1f}%")

if __name__ == "__main__":
    shorts_to_view = [
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
        process_shorts_continuously(shorts_to_view, use_proxies=True)
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        logger.info("Script execution completed")