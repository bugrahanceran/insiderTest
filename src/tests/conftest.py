import pytest
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture(scope="function")
def driver():
    """
    Bu fixture her test fonksiyonundan once calisir ve sonra kapanir.
    Environment variable'a göre Remote veya Local driver baslatir.
    """
    # K8s içindeki Chrome Node servisinin DNS adı veya IP'si
    # Default olarak 'chrome-node-service' (K8s Service adımız olacak)
    hub_host = os.environ.get('SELENIUM_HUB_HOST', 'chrome-node-service')
    hub_port = os.environ.get('SELENIUM_HUB_PORT', '4444')
    
    # Headless Chrome seçenekleri
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # GUI olmadan çalış
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    print(f"\n[INFO] Connecting to Selenium Grid at: http://{hub_host}:{hub_port}/wd/hub")

    try:
        # Remote WebDriver (K8s içindeki Chrome Node'a bağlanır)
        driver = webdriver.Remote(
            command_executor=f'http://{hub_host}:{hub_port}/wd/hub',
            options=chrome_options
        )
        driver.implicitly_wait(10) # Element bulamazsa 10sn bekle
        yield driver
        
    except Exception as e:
        print(f"\n[ERROR] Driver could not start: {e}")
        raise e
        
    finally:
        # Test bitince tarayıcıyı kapat (Teardown)
        if 'driver' in locals():
            driver.quit()