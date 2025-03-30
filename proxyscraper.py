from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_short_view(url):
    chrome_options = Options()
    chrome_options.add_argument("--window-size=412,732")  # Mobile viewport
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1")
    
    # Anti-detection configurations
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Add additional stealth options
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    
    # Create a new driver instance
    driver = webdriver.Chrome(options=chrome_options)
    
    # Execute CDP commands to mask WebDriver
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
        
        # Wait for initial page load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "ytd-app"))
        )
        logger.info("Page loaded successfully")
        
        # Wait a bit for any popups to appear
        time.sleep(3)
        
        # Dismiss any dialogs or popups that might interfere
        try:
            # Try different methods to dismiss popups
            popups = driver.find_elements(By.CSS_SELECTOR, "tp-yt-paper-dialog, ytd-popup-container")
            for popup in popups:
                driver.execute_script("arguments[0].remove();", popup)
                
            # Alternative method to dismiss sign-in prompt
            dismiss_buttons = driver.find_elements(By.CSS_SELECTOR, 
                "button.yt-spec-button-shape-next, .ytd-button-renderer, .yt-spec-touch-feedback-shape--touch-response-inverse")
            for button in dismiss_buttons:
                if "sign in" not in button.text.lower() and "later" in button.text.lower():
                    button.click()
                    logger.info("Dismissed a popup")
                    time.sleep(1)
        except Exception as e:
            logger.warning(f"Error handling popups: {str(e)}")
        
        # Simulate random human-like movements to avoid detection
        actions = ActionChains(driver)
        actions.move_by_offset(random.randint(5, 20), random.randint(5, 20)).perform()
        time.sleep(random.uniform(0.5, 1.5))
        actions.click().perform()
        
        # Wait specifically for the video element with increased timeout
        logger.info("Waiting for video element...")
        video = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "video.html5-main-video"))
        )
        logger.info("Video element found")
        
        # Make sure video is in view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", video)
        time.sleep(1)
        
        # Try to start playback
        driver.execute_script("arguments[0].play()", video)
        logger.info("Play command executed")
        
        # Check if video is actually playing
        time.sleep(3)
        is_playing = driver.execute_script("return !arguments[0].paused", video)
        
        if not is_playing:
            logger.warning("Video not playing, trying to click on it")
            actions = ActionChains(driver)
            actions.move_to_element(video).click().perform()
            time.sleep(2)
        
        # Get video duration
        try:
            duration = driver.execute_script("return arguments[0].duration", video)
            if duration:
                logger.info(f"Video duration: {duration} seconds")
                watch_time = min(60, duration * 0.8)  # Watch 80% or 60s max
            else:
                logger.warning("Could not determine video duration, using default")
                watch_time = 30
        except:
            logger.warning("Error getting video duration, using default watch time")
            watch_time = 30
        
        # Simulate engagement
        logger.info(f"Watching for {watch_time} seconds")
        
        # Instead of just waiting, interact periodically
        watch_start = time.time()
        while time.time() - watch_start < watch_time:
            # Periodically check if video is still playing
            is_playing = driver.execute_script("return !arguments[0].paused", video)
            if not is_playing:
                logger.warning("Video paused, attempting to resume")
                driver.execute_script("arguments[0].play()", video)
            
            # Simulate scroll/interactions every few seconds
            if random.random() < 0.3:
                offset_y = random.randint(-10, 10)
                actions.move_by_offset(0, offset_y).perform()
            
            time.sleep(2)
        
        logger.info("Successfully watched short!")
        return True
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        # Take screenshot for debugging
        try:
            driver.save_screenshot('error.png')
            logger.info("Screenshot saved as 'error.png'")
        except:
            logger.warning("Could not save screenshot")
        return False
    finally:
        driver.quit()

def process_multiple_shorts(urls):
    results = []
    for url in urls:
        success = simulate_short_view(url)
        results.append((url, success))
        # Random delay between videos to appear more natural
        time.sleep(random.uniform(5, 15))
    
    # Report results
    logger.info("===== VIEWING RESULTS =====")
    for url, success in results:
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"{status}: {url}")

if __name__ == "__main__":
    # Example usage with a single short
    # simulate_short_view("https://www.youtube.com/shorts/lOVVGfSKCv4")
    
    # Example usage with multiple shorts
    shorts_to_view = [
        "https://www.youtube.com/shorts/lOVVGfSKCv4",
        # Add more short URLs here
    ]
    process_multiple_shorts(shorts_to_view)