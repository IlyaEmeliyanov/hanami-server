
# Importing modules
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

import time

# Creating and configuring the class for WebScraper
# Pattern used: singleton
class WebScraper(object):
    def __init__(self, url): # managing the 1st initialiazation of the WebScraper singleton
        self.config(url)
        print("Connected to: ", self.URL)

    def __new__(cls, url): # used for creating a unique instance of a class
        if not hasattr(cls, 'instance'):
            cls.instance = super(WebScraper, cls).__new__(cls)
        return cls.instance

    def config(self, url):
        self.URL = url
        
        options = Options()
        options.add_experimental_option("detach", True)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        driver.get(self.URL)
        driver.maximize_window()

        self.driver = driver

    def login(self, username, password):
        username_input = self.driver.find_element(By.ID, "lbName")
        password_input = self.driver.find_element(By.ID, "lbPad")
        submit_button = self.driver.find_element(By.XPATH, "//div[contains(@class, 'ui-btn ui-input-btn ui-shadow')]//input")

        username_input.send_keys(username)
        password_input.send_keys(password)

        submit_button.click()


    def process(self, queue, table, dishes):
        # IVANO, STAY HYDRATED 💧

        print("TABLE=", table)
        print("DISH=", dishes)

        try:
            time.sleep(1)
            # Get all tables
            xpath_table_item = "//div//ul[contains(@class, 'ui-listview')]//li//a[contains(@class, 'ui-btn')]"
            table_elements = self.driver.find_elements(By.XPATH, xpath_table_item)
            table_state = False
            for table_item in table_elements:
                if table_item.get_attribute("innerHTML") == table:
                    if table_item.value_of_css_property("bakground-color") == "#66D972":
                        table_state = True


            # Fill search text field with the table number
            search_input = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "search")))
            search_input.send_keys(table) # send the table's number
            search_input.send_keys(Keys.RETURN) # hitting return for selecting the table

            time.sleep(2) # Make sure all the elements of the page load properly
            # Fill search text field with the dish number
            search_input_dish = self.driver.find_element(By.ID, "search")
            for dish_data in dishes:
                search_input_dish.send_keys(dish_data["dish"])
                for _ in range(dish_data["qty"]):
                    time.sleep(0.5)
                    search_input_dish.send_keys(Keys.RETURN)

            time.sleep(0.5) # Make sure all the elements of the page load properly
            xpath_submit_button = "//div[contains(@id, 'mfooter')]//div//ul[contains(@class, 'ui-grid-b')]//ul[contains(@class, 'ui-block-c ui-grid-c')]//li[contains(@class, 'ui-block-d')]//a"
            submit_button = self.driver.find_element(By.XPATH, xpath_submit_button)
            time.sleep(0.5)
            submit_button.click()
            if table_state == False:
                xpath_complete_button = "//div[contains(@class, 'ui-controlgroup-controls')]//a"
                complete_button = self.driver.find_element(By.XPATH, xpath_complete_button)
                complete_button.click()
                time.sleep(0.5)
        except Exception as exception:
            print(f"\n[❌] Something went wrong: {exception}")

        try: # trying to deque the last order
            queue.get() 
        except Exception as exception:
            print(f"\n[❌] Something went wrong: {exception}")