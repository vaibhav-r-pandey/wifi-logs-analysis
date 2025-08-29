import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import test

# Configure logging
def configure_logging():
    logging.basicConfig(level=logging.INFO)  # Set the desired logging level

# Login to the website
def login(driver, url):
    driver.get(url)
    time.sleep(5)  # Wait for initial page load
    
    try:
        # Wait for the login button to be present and clickable
        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, 'idSIButton9'))
        )
        login_button.click()
        logging.info("Successfully clicked login button")
        
        # Wait a bit and try to click again if needed
        time.sleep(3)
        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'idSIButton9'))
            )
            login_button.click()
            logging.info("Successfully clicked login button second time")
        except:
            logging.info("Second login button click not needed or button not found")
            
    except Exception as e:
        logging.error(f"Login button with ID 'idSIButton9' not found: {e}")
        # Try alternative selectors
        try:
            # Common Microsoft login button alternatives
            alternative_selectors = [
                "input[type='submit'][value*='Sign']",
                "input[type='submit'][value*='Next']", 
                "button[type='submit']",
                "*[id*='Button']",
                "*[class*='button']"
            ]
            
            for selector in alternative_selectors:
                try:
                    button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    button.click()
                    logging.info(f"Successfully clicked button with selector: {selector}")
                    break
                except:
                    continue
            else:
                logging.error("No suitable login button found with any selector")
                
        except Exception as alt_e:
            logging.error(f"Alternative login methods also failed: {alt_e}")
    
    time.sleep(10)


# Get the table data
def get_table_data(driver):
    # Wait for the page to load completely using WebDriverWait
    #driver.execute_script("document.body.style.zoom = '25%'")
    #time.sleep(40)

    # Extract the discussion content from the page
    html_data = driver.page_source
    # Assuming the HTML snippet is stored in a variable called html_data
    soup1 = BeautifulSoup(html_data, 'html.parser')
    
    attachments_board_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//li[@aria-label="Attachments"]')))
    attachments_board_tab.click()
    time.sleep(10)

        
    html_content = driver.page_source
    soup2 = BeautifulSoup(html_content, 'html.parser')

    # Locate the target div containing spans
    file_div = soup2.find('div', class_='ag-center-cols-viewport')
    if file_div is None:
        raise ValueError("The div with class 'ag-center-cols-viewport' was not found")

    # Find all spans within the div
    spans_list = file_div.find_all('span')
    if not spans_list:
        raise ValueError("No spans were found within the div")

    # Iterate through spans and click those containing the keyword "err"
    for span in spans_list:
        if 'err' in span.text or 'Err' in span.text or 'dmesg' in span.text or 'Dmesg' in span.text or 'error' in span.text or 'Error' in span.text or 'WAPI' in span.text or 'issue' in span.text or 'log' in span.text or 'logs' in span.text:
            try:
                xpath = "//button[@aria-label='"+span.text+"']"
                print(xpath)
                button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
                )
                button.click()
                time.sleep(10)
                logging.info("Successfully clicked on the error file.")
            except Exception as e:
                logging.error(f"Failed to find or click the error file: {e}")

    handles = driver.window_handles
    driver.switch_to.window(handles[1])

    # Get the HTML of the new page
    html_content = driver.page_source
    lines = html_content.splitlines()
    #driver.quit()
    start_extract = False
    result_lines = []

    for line in lines:
        #if "dhd" in line:
        #    start_extract = True
        #if start_extract:
        result_lines.append(line)

    # Join the result lines into a single string
    result_html = "\n".join(result_lines)

    print(len(result_html))
    if len(result_html) >= 131072:
        x = len(result_html) - 131072
        result_html = result_html[x:]

    print(len(result_html))

    test_prompt = '\n You are given a dmesg log for wifi chip bringup and normal funtioning, now for starting with the case we need to get an analysis of the case logs. Go through the logs file and provide me a detailed analysis of the logs and the path I should follow to debug the issue. Please provide a detailed analysis with function names if possible input is in the form of a text variable, where each line may or may not contain logs related to wifi bringup and normal funtioning.'
    test_logs = result_html+ test_prompt
    print(test_logs)
    output = test.test_chat_completion_api(test_logs)
    print(output)
    with open(f"response.md", 'w') as f:
        f.write(output)
    

    time.sleep(5)
    return output


def run_analysis(url):
    # Configure logging
    configure_logging()

    # Create a new instance of the Edge browser
    SelService = Service(executable_path=r'msedgedriver.exe')
    driver_options = webdriver.EdgeOptions()
    driver_options.add_argument("--no-sandbox")
    driver = webdriver.Edge(service=SelService, options=driver_options)
    driver.maximize_window()

    # Login to the website
    login(driver, url)
    get_table_data(driver)



if __name__ == "__main__":
    # Specify the URL
    url = "https://ifxcasemanagement.crm4.dynamics.com/main.aspx?appid=4d4c3d73-64de-ec11-bb3c-002248810ede&pagetype=entityrecord&etn=incident&id=80a09211-1826-ee11-a81c-6045bd870ed4"

    # Configure logging
    configure_logging()

    # Create a new instance of the Edge browser
    SelService = Service(executable_path=r'msedgedriver.exe')
    driver_options = webdriver.EdgeOptions()
    driver = webdriver.Edge(service=SelService, options=driver_options)
    driver.maximize_window()

    # Login to the website
    login(driver, url)
    get_table_data(driver)

    