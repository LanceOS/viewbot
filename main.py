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
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File to store proxy list
PROXY_FILE = "proxylist.txt"

# Global flag to control execution
running = True

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
        "https://www.us-proxy.org/"
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    for source in sources:
        try:
            logger.info(f"Fetching proxies from {source}")
            response = requests.get(source, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
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
            proxies = {
                "http": f"http://{proxy}",
                "https": f"https://{proxy}"
            }
            response = requests.get(test_url, proxies=proxies, timeout=5)
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

def simulate_short_view(url, proxy=None):
    chrome_options = Options()
    chrome_options.add_argument("--window-size=412,732")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')
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
        logger.info(f"Opening URL: {url}")
        driver.get(url)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "ytd-app")))
        logger.info("Page loaded successfully")
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
        driver.execute_script("window.scrollTo(0, 100);")
        time.sleep(1)
        viewport_height = driver.execute_script("return window.innerHeight;")
        viewport_width = driver.execute_script("return window.innerWidth;")
        center_x = viewport_width / 2
        center_y = viewport_height / 2
        driver.execute_script(f"""
            const clickEvent = new MouseEvent('click', {{
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: {center_x},
                clientY: {center_y}
            }});
            document.elementFromPoint({center_x}, {center_y}).dispatchEvent(clickEvent);
        """)
        logger.info(f"Clicked at viewport center ({center_x}, {center_y})")
        time.sleep(2)
        
        logger.info("Searching for video element...")
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
                driver.save_screenshot('no_video.png')
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
        
        while time.time() - start_time < watch_time:
            if not running:
                logger.info("Stopping current view early due to shutdown signal")
                break
            
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
            
            # Open comments section at least once, at a random point
            if not comments_opened and random.random() < 0.3:  # 30% chance per check
                try:
                    # Find the comments button (often a speech bubble icon or "Comments" text)
                    comments_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Show comments'] | //ytm-comment-section-renderer"))
                    )
                    actions = ActionChains(driver)
                    actions.move_to_element(comments_button).click().perform()
                    logger.info("Opened comments section")
                    comments_opened = True
                    time.sleep(2)  # Pause briefly to simulate reading comments
                except TimeoutException:
                    logger.warning("Comments button not found, trying alternative method")
                    driver.execute_script("""
                        const comments = document.querySelector('ytm-comment-section-renderer, #comments-button');
                        if (comments) comments.click();
                    """)
                    if driver.execute_script("return !!document.querySelector('ytm-comment-section-renderer.visible');"):
                        logger.info("Opened comments section via JavaScript")
                        comments_opened = True
                        time.sleep(2)
                    else:
                        logger.warning("Could not open comments section")
            
            # Small random scroll to simulate engagement
            if random.random() < 0.2:
                small_scroll = random.randint(-10, 10)
                driver.execute_script(f"window.scrollBy(0, {small_scroll});")
            time.sleep(3)
        
        if not comments_opened:
            # Ensure comments are opened at least once if not triggered earlier
            try:
                comments_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Show comments'] | //ytm-comment-section-renderer"))
                )
                actions = ActionChains(driver)
                actions.move_to_element(comments_button).click().perform()
                logger.info("Opened comments section (forced at end)")
                time.sleep(2)
            except TimeoutException:
                logger.warning("Forced comments opening failed")
        
        logger.info("Successfully watched short!")
        return True
    except Exception as e:
        logger.error(f"Failed: {str(e)}")
        try:
            driver.save_screenshot('error.png')
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
                delay = random.uniform(15, 55)
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