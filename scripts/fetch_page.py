"""Fetch a web page and print it as Markdown."""

import os
import sys
import time

import requests
from html_to_markdown import convert
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver

# Selenium Manager uses the system Chrome if it is this major version, and otherwise
# downloads this Chrome for Testing release into ~/.cache/selenium. Either way it fetches
# the matching driver itself and ignores any chromedriver on PATH.
CHROME_VERSION = "158"
BLOCKED_STATUS_CODES = (401, 403)
CHALLENGE_TIMEOUT_SECONDS = 20
CHALLENGE_POLL_SECONDS = 1


class BotChallengeError(RuntimeError):
    """Raised when a site keeps serving a bot-check page instead of its content."""


def is_challenge_page(driver: WebDriver) -> bool:
    """Report whether the browser is showing a Cloudflare or DataDome bot-check page.

    Args:
        driver: The browser, after navigating to a page.

    Returns:
        True if the current page is a bot check rather than the site's content.
    """
    return (
        driver.title.startswith("Just a moment")
        or "captcha-delivery.com" in driver.page_source
    )


def fetch_with_browser(url: str) -> str:
    """Fetch a page's rendered HTML with headless Chrome.

    Args:
        url: The page to open.

    Returns:
        The HTML of the page after it has loaded.

    Raises:
        BotChallengeError: If the site is still showing a bot-check page after
            CHALLENGE_TIMEOUT_SECONDS.
    """
    os.environ.setdefault("SE_SKIP_DRIVER_IN_PATH", "true")
    options = Options()
    options.browser_version = CHROME_VERSION
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1400,1000")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)
    try:
        # Headless Chrome announces itself in its user agent, which bot checks reject.
        user_agent = driver.execute_script("return navigator.userAgent")
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": user_agent.replace("HeadlessChrome", "Chrome")},
        )
        driver.get(url)
        # A bot check that passes redirects to the real page a few seconds after loading.
        deadline = time.monotonic() + CHALLENGE_TIMEOUT_SECONDS
        while is_challenge_page(driver):
            if time.monotonic() > deadline:
                raise BotChallengeError(
                    f"{url} still shows a bot-check page after "
                    f"{CHALLENGE_TIMEOUT_SECONDS}s; the site is blocking automated access"
                )
            time.sleep(CHALLENGE_POLL_SECONDS)
        return driver.page_source
    finally:
        driver.quit()


def fetch_page(url: str) -> str:
    """Fetch a page and convert it to Markdown.

    A plain HTTP request is tried first. If the site refuses it with 401 or 403, the page
    is fetched again with headless Chrome.

    Args:
        url: The page to fetch.

    Returns:
        The page as Markdown, or its raw HTML if the conversion produces nothing.

    Raises:
        requests.HTTPError: If the site returns an error status other than 401 or 403.
        BotChallengeError: If the site blocks headless Chrome as well.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
    except requests.HTTPError as e:
        if e.response is None or e.response.status_code not in BLOCKED_STATUS_CODES:
            raise
        print(
            f"Got a {e.response.status_code}, retrying with headless Chrome...",
            file=sys.stderr,
        )
        html = fetch_with_browser(url)

    return convert(html).content or html


if __name__ == "__main__":
    print(fetch_page(sys.argv[1]))
