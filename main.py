from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import re
import time
import pandas as pd

ua = UserAgent(os='linux', browsers=['edge', 'chrome'], min_percentage=1.3)
random_user_agent = ua.random

# Keep the browser open after the program finishes
options = Options()
options.add_experimental_option("detach", True)
options.add_argument(f"user-agent={random_user_agent}")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = ("https://www.openrent.co.uk/properties-to-rent/london?term=London.&area=20&prices_min=1000&prices_max=2000"
       "&bedrooms_min=0&bedrooms_max=2&viewingProperty=2")

driver.get(url)

try:
    # Wait for the property-data container to be present
    element_present = EC.presence_of_element_located((By.ID, "property-data"))
    WebDriverWait(driver, 10).until(element_present)

    # Wait for the first item to be present before proceeding
    element_present = EC.presence_of_element_located((By.CLASS_NAME, "pli"))
    WebDriverWait(driver, 10).until(element_present)

except TimeoutException as e:
    print(f"Timed out waiting for elements: {e}")

# Now that the page has loaded, you can proceed to parse it
soup = BeautifulSoup(driver.page_source, "lxml")

## Initialize the previous page height
prev_page_height = 0

scraped_data = []

while True:
    # Scroll down to the bottom of the page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait for a short moment to allow new data to load
    time.sleep(10)

    # Get the updated page source
    soup = BeautifulSoup(driver.page_source, "lxml")

    # Find the property container in the updated page source
    container = soup.find(id="property-data")

    # Get the current page height
    current_page_height = driver.execute_script("return document.body.scrollHeight")

    # Check if the page height has remained the same (no new data loaded)
    if current_page_height == prev_page_height:
        break

    # Update the previous page height
    prev_page_height = current_page_height

    for item in container.find_all("a", class_="pli clearfix"):
        title = item.find("span", class_="banda pt listing-title").text.strip()
        price = item.select_one(".listing-info .price-location h2").text
        furnishing = item.select_one("div.location-detail ul.lic.clearfix li:last-child").get_text(strip=True)
        href = item.get("href")

        # Extract the "Last Updated" text
        last_updated_text = item.find('div', class_='timeStamp')
        if last_updated_text:
            text = last_updated_text.text.strip()
            match = re.search(r'Last Updated\s*around\s*(\d+)\s*(hour|minute|day)s? ago', text)
            if match:
                value = int(match.group(1))
                unit = match.group(2)

                # Check if value is within the desired range and unit is either "hour", "minute", or "day", and adjust the plural form
                if value is not None and unit in ["hour", "minute", "day"]:
                    if unit == "day" and 0 < value <= 1:

                        # Append data to the list for pandas
                        data = {
                            "Title": title,
                            "Furnishing": furnishing,
                            "Price": price,
                            "Last Updated": f"{value} {unit}{'s' if value != 1 else ''} ago",
                            "URL": f"https://www.openrent.co.uk{href}"
                        }
                        scraped_data.append(data)
                    elif unit == "hour" and 0 < value <= 23:

                        # Append data to the list for pandas
                        data = {
                            "Title": title,
                            "Furnishing": furnishing,
                            "Price": price,
                            "Last Updated": f"{value} {unit}{'s' if value != 1 else ''} ago",
                            "URL": f"https://www.openrent.co.uk{href}"
                        }
                        scraped_data.append(data)
                    elif unit == "minute" and 0 < value < 60:

                        # Append data to the list for pandas
                        data = {
                            "Title": title,
                            "Furnishing": furnishing,
                            "Price": price,
                            "Last Updated": f"{value} {unit}{'s' if value != 1 else ''} ago",
                            "URL": f"https://www.openrent.co.uk{href}"
                        }
                        scraped_data.append(data)

# Create a DataFrame from the list of dictionaries
df = pd.DataFrame(scraped_data, columns=["Title", "Price", "Furnishing", "Price", "Last Updated", "URL"],
                  index=range(1, len(scraped_data) + 1))

# Print the DataFrame
print(df)

print("Before saving CSV")
# Save the DataFrame to a CSV file
df.to_csv("scraped_data2.csv", index_label="No")
print("After saving CSV")
driver.quit()
