from html_to_markdown import convert
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from chromedriver_py import binary_path


def fetch_page(url: str) -> str:

    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
    except requests.HTTPError as e:
        if e.response and e.response.status_code == 403:
            print("Got a 403, trying with selenium...")
            svc = webdriver.ChromeService(executable_path=binary_path)
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(service=svc, options=chrome_options)
            driver.get(url)
            html = driver.page_source
            driver.close()
        raise

    return convert(html).content or response.text


if __name__ == "__main__":
    import sys

    print(fetch_page(sys.argv[1]))
