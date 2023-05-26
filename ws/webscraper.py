
# Importing modules
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from webdriver_manager.chrome import ChromeDriverManager

import time

from multiprocessing import Process
from queue import Queue

# Creating and configuring the class for WebScraper
# Pattern used: singleton
class WebScraper(object):
    def __init__(self, url): # managing the 1st initialiazation of the WebScraper singleton
        self.config(url)
        self.table = ""
        self.orders = []
        self.is_completed = False
        self.ws_process = None
        self.process_queue = Queue()
        print("Connected to: ", self.URL)

    def __new__(cls, url): # used for creating a unique instance of a class
        if not hasattr(cls, 'instance'):
            cls.instance = super(WebScraper, cls).__new__(cls)
        return cls.instance

    def get_chrome_options(self) -> Options:
        """Sets chrome options for Selenium.
        Chrome options for headless browser is enabled.
        """
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_prefs = {}
        # chrome_options.experimental_options["prefs"] = chrome_prefs
        # chrome_prefs["profile.default_content_settings"] = {"images": 2}
        return chrome_options

    def run(self, table, orders):
        self.process_queue.put({"table": table, "orders": orders})
        if self.ws_process is None or not self.ws_process.is_alive(): # process_queue is empty
            self.ws_process = Process(target=self.process_debug)
            self.ws_process.start()
        else: # process_queue is already processing an order
            print("[LOG] Processing ...")


    def config(self, url):
        self.URL = url
        
        # driver = webdriver.Remote("http://selenium:4444/wd/hub", desired_capabilities=DesiredCapabilities.CHROME)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.get_chrome_options())

        driver.get(self.URL)
        driver.maximize_window()

        self.driver = driver

    def login_debug(self, username, password):

        print("[LOG] Login in MERIN")

        username_input = self.driver.find_element(By.CLASS_NAME, "username")
        password_input = self.driver.find_element(By.CLASS_NAME, "password")
        submit_button = self.driver.find_element(By.CLASS_NAME, "login__btn")

        username_input.send_keys(username)
        password_input.send_keys(password)

        submit_button.click()

    def process_debug(self):

        print("[LOG] Start processing MERIN")

        table, orders = self.process_queue.get().values()

        try:
            time.sleep(1)

            table_input = self.driver.find_element(By.CLASS_NAME, "table")
            table_input.send_keys(table)

            time.sleep(1)

            dish_input = self.driver.find_element(By.CLASS_NAME, "dish")
            enter_button = self.driver.find_element(By.CLASS_NAME, "enter__btn")

            for order in orders:
                dish_input.send_keys(order)
                time.sleep(0.5)
                enter_button.click()
                dish_input.clear()
                time.sleep(0.5)

            time.sleep(2)

            table_input.clear()
            dish_input.clear()

            submit_button = self.driver.find_element(By.CLASS_NAME, "order__btn")
            submit_button.click()

            time.sleep(1)

        except Exception as exception:
            print(f"[ERROR] Something went wrong in process_debug {exception}")

        self.is_completed = True

        # get from process_queue and recursive call to process_debug
        if not self.process_queue.empty():
            print("BLABLBALBALBALBAL")
            self.is_completed = False
            self.ws_process = Process(target=self.process_debug)
            self.ws_process.start()

        print("[LOG] End processing MERIN")

    def login(self, username, password):
        username_input = self.driver.find_element(By.ID, "lbName")
        password_input = self.driver.find_element(By.ID, "lbPad")
        submit_button = self.driver.find_element(By.XPATH, "//div[contains(@class, 'ui-btn ui-input-btn ui-shadow')]//input")

        username_input.send_keys(username)
        password_input.send_keys(password)

        submit_button.click()

    def process(self):
        # IVANO, STAY HYDRATED 💧

        print("TABLE=", self.table)
        print("DISH=", self.orders)

        try:
            time.sleep(1)
            # Get all tables
            xpath_table_item = "//div//ul[contains(@class, 'ui-listview')]//li//a[contains(@class, 'ui-btn')]"
            table_elements = self.driver.find_elements(By.XPATH, xpath_table_item)
            table_state = False
            for table_item in table_elements:
                if table_item.get_attribute("innerHTML") == self.table:
                    if table_item.value_of_css_property("background-color") == "#66D972":
                        table_state = True

            # Fill search text field with the table number
            search_input = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "search")))
            search_input.send_keys(self.table) # send the table's number
            search_input.send_keys(Keys.RETURN) # hitting return for selecting the table

            time.sleep(2) # Make sure all the elements of the page load properly
            # Fill search text field with the dish number
            search_input_dish = self.driver.find_element(By.ID, "search")
            for order in self.orders:
                search_input_dish.send_keys(order)
                search_input_dish.send_keys(Keys.RETURN)
                
            time.sleep(0.5) # Make sure all the elements of the page load properly
            xpath_submit_button = "//div[contains(@id, 'mfooter')]//div//ul[contains(@class, 'ui-grid-b')]//ul[contains(@class, 'ui-block-c ui-grid-c')]//li[contains(@class, 'ui-block-d')]//a"
            submit_button = self.driver.find_element(By.XPATH, xpath_submit_button)
            time.sleep(0.5)
            submit_button.click()
            if table_state == False:
                time.sleep(1)
                try:
                    xpath_complete_button = "//div[contains(@class, 'ui-controlgroup-controls')]//a"
                    complete_button = self.driver.find_element(By.XPATH, xpath_complete_button)
                    complete_button.click()
                except NoSuchElementException:
                    print("[ERROR]: Element doesn't exist")
        except Exception as exception:
            print(f"\n[ERROR] Something went wrong in process: {exception}")

        self.is_completed = True

        