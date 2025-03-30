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
        
        # Wait for initial page load with longer timeout
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "ytd-app"))
        )
        logger.info("Page loaded successfully")
        
        # Wait a bit for any popups to appear
        time.sleep(5)
        
        # Dismiss any dialogs or popups that might interfere
        try:
            # Use JavaScript to dismiss common YouTube popups
            driver.execute_script("""
                // Remove any visible dialogs
                const dialogs = document.querySelectorAll('tp-yt-paper-dialog, ytd-popup-container');
                dialogs.forEach(dialog => dialog.remove());
                
                // Remove any modal overlays
                const overlays = document.querySelectorAll('.ytd-consent-bump-v2-lightbox, ytd-consent-bump-v2-lightbox');
                overlays.forEach(overlay => overlay.remove());
                
                // Clear fixed elements that might intercept clicks
                const fixedElements = document.querySelectorAll('.ytd-popup-container, .ytd-mealbar-promo-renderer');
                fixedElements.forEach(el => el.remove());
            """)
            logger.info("Attempted to remove popups via JavaScript")
        except Exception as e:
            logger.warning(f"Error handling popups: {str(e)}")
        
        # Wait a moment for things to settle
        time.sleep(2)
        
        # Target the video player area directly with JavaScript
        logger.info("Attempting to find and interact with the video player...")
        try:
            # First scroll to ensure we're in the right area
            driver.execute_script("window.scrollTo(0, 100);")
            time.sleep(1)
            
            # Click in the center of the viewport where the video typically is
            viewport_height = driver.execute_script("return window.innerHeight;")
            viewport_width = driver.execute_script("return window.innerWidth;")
            
            # Calculate center of viewport
            center_x = viewport_width / 2
            center_y = viewport_height / 2
            
            # Use JavaScript to create and dispatch a click event in the center
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
        except Exception as e:
            logger.warning(f"Error with center click: {str(e)}")
        
        # Now try to locate and interact with the video element
        logger.info("Searching for video element...")
        try:
            # Use a more lenient selector to find the video
            video_selector = "video"
            video = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, video_selector))
            )
            logger.info("Video element found!")
            
            # Scroll the video into center view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", video)
            time.sleep(1)
            
            # Get the dimensions and position of the video
            video_rect = driver.execute_script("""
                const rect = arguments[0].getBoundingClientRect();
                return {
                    top: rect.top,
                    left: rect.left,
                    width: rect.width,
                    height: rect.height
                };
            """, video)
            
            logger.info(f"Video position: {video_rect}")
            
            # Click in the center of the video using ActionChains
            try:
                video_center_x = video_rect['left'] + (video_rect['width'] / 2)
                video_center_y = video_rect['top'] + (video_rect['height'] / 2)
                
                # Check if the center of the video is visible in the viewport
                is_visible = driver.execute_script(f"""
                    return (
                        {video_center_x} >= 0 &&
                        {video_center_y} >= 0 &&
                        {video_center_x} <= window.innerWidth &&
                        {video_center_y} <= window.innerHeight
                    );
                """)
                
                if is_visible:
                    logger.info(f"Video center is visible at ({video_center_x}, {video_center_y})")
                    actions = ActionChains(driver)
                    actions.move_to_element_with_offset(video, video_rect['width']/2, video_rect['height']/2)
                    actions.click()
                    actions.perform()
                else:
                    logger.warning("Video center is not in viewport, using JavaScript click instead")
                    driver.execute_script("arguments[0].click();", video)
            except ElementClickInterceptedException:
                logger.warning("Click intercepted, using JavaScript to play video")
                driver.execute_script("arguments[0].play();", video)
        except TimeoutException:
            logger.warning("Could not find video with specific selector, trying a direct approach")
            # Try to find any video element
            videos = driver.find_elements(By.TAG_NAME, "video")
            if videos:
                logger.info(f"Found {len(videos)} video elements with tag search")
                video = videos[0]
                driver.execute_script("arguments[0].play();", video)
            else:
                logger.error("No video elements found on the page")
                driver.save_screenshot('no_video.png')
                return False
        
        # Check if video is actually playing
        time.sleep(3)
        try:
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
                logger.warning("Video not playing, attempting another method")
                driver.execute_script("""
                    const videos = document.querySelectorAll('video');
                    videos.forEach(v => v.play());
                """)
                time.sleep(2)
        except Exception as e:
            logger.warning(f"Error checking playback: {str(e)}")
        
        # Get video duration
        try:
            duration = driver.execute_script("""
                const videos = document.querySelectorAll('video');
                for (let i = 0; i < videos.length; i++) {
                    if (videos[i].duration) return videos[i].duration;
                }
                return 30;
            """)
            logger.info(f"Video duration: {duration} seconds")
            watch_time = min(60, duration * 0.8)  # Watch 80% or 60s max
        except:
            logger.warning("Error getting video duration, using default watch time")
            watch_time = 30
        
        # Watch the video
        logger.info(f"Watching for {watch_time} seconds")
        start_time = time.time()
        while time.time() - start_time < watch_time:
            # Periodically check if video is still playing
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
            
            # Wait a bit before next check
            time.sleep(3)
        
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
    # # You can test with a single short
    # simulate_short_view("https://www.youtube.com/shorts/lOVVGfSKCv4")
    
    # Or process multiple shorts
    shorts_to_view = [
        "https://www.youtube.com/shorts/lOVVGfSKCv4",  # Example Short 1
        "https://www.youtube.com/shorts/OPSV7kjrnw8",  # Example Short 2
        "https://www.youtube.com/shorts/EuqmysuhS30",  # Example Short 3
        "https://www.youtube.com/shorts/BrsWRRqOGNk",
        "https://www.youtube.com/shorts/-yw5boY3eB4",
        "https://www.youtube.com/shorts/GaFQx3_bx7k",
        "https://www.youtube.com/shorts/F-OOCA9pxP0",
        "https://www.youtube.com/shorts/QUSrYy0Ls-w"
    ]
    process_multiple_shorts(shorts_to_view)