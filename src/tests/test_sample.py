import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_homepage_title(driver):
    """
    Test the homepage title of the site.
    """
    print("[TEST] Navigating to The-Internet homepage...")
    driver.get("https://the-internet.herokuapp.com/")
    
    title = driver.title
    print(f"[TEST] Page Title: {title}")
    assert "The Internet" in title

def test_login_process(driver):
    """
    Navigate to the login page and attempt to log in.
    """
    print("[TEST] Navigating to the login page...")
    driver.get("https://the-internet.herokuapp.com/login")
    
    # Wait for username and password fields
    username_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    password_input = driver.find_element(By.ID, "password")
    
    # (Correct credentials: tomsmith / SuperSecretPassword!)
    username_input.send_keys("tomsmith")
    password_input.send_keys("SuperSecretPassword!")
    
    # Click the login button
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    print("[TEST] Login information submitted.")
    
    # Check the successful login message (flash success message)
    success_message = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".flash.success"))
    )
    
    print(f"[TEST] Message: {success_message.text}")
    assert "You logged into a secure area" in success_message.text