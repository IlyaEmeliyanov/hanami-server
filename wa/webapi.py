
# Importing modules
from flask import Flask, request
from pymongo import *
from dotenv import load_dotenv
import certifi # import this module if having TLS certificate issues

from bson.json_util import dumps

from os import getenv

# Importing ws
from ws.webscraper import WebScraper

class Server:
    def __init__(self) -> None:
        # Config server settings
        self.config()

    def run(self):
        # @GET requests
        @self.app.route("/")
        def dishes():
            collection = self.db["dishes"]
            obj = []
            for item in collection.find():
                obj.append(item)
            return dumps(obj)
        
        @self.app.route("/drinks")
        def drinks():
            collection = self.db["drinks"]
            obj = []
            for item in collection.find():
                obj.append(item)
            return dumps(obj)
            
        @self.app.route("/beers")
        def beers():
            collection = self.db["beers"]
            obj = []
            for item in collection.find():
                obj.append(item)
            return dumps(obj)
        
        @self.app.route("/desserts")
        def desserts():
            collection = self.db["desserts"]
            obj = []
            for item in collection.find():
                obj.append(item)
            return dumps(obj)

        @self.app.route("/menu")
        def menu():
            collection = self.db["menu"]
            obj = []
            for item in collection.find():
                obj.append(item)
            return dumps(obj)
        
        # @POST requests
        @self.app.route("/order", methods=["POST"])
        def order():
            if request.method == "POST":
                json_content = request.get_json() # json_content = {data: {table: 3, dish: "001", qty: 3}}
                try: # handling exception in case of ws failure
                    self.ws.login("a", "a")
                    self.ws.process(json_content['data']) # processing the order: table=3, dish="001", qty=3
                except Exception as exception:
                    print(f"\n[❌] Something went wrong: {exception}")
                    
            return dumps({"status": "success", "statusCode": 201})

        self.app.run(port=self.PORT)
    
    def config(self):
        load_dotenv() # loading environment variables
        DB_USERNAME = getenv('DB_USERNAME')
        DB_PASSWORD = getenv('DB_PASSWORD')
        DB_CLUSTER = getenv('DB_CLUSTER')
        COLLECTION_NAME = getenv('COLLECTION_NAME')

        # Database config
        client = MongoClient(f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@{DB_CLUSTER}/?retryWrites=true&w=majority", tlsCAFile=certifi.where())
        self.db = client[COLLECTION_NAME]

        # Web server with flask
        self.PORT = getenv('PORT')
        self.app = Flask(__name__)

        # Web scraper config
        self.WS_URL = getenv("WS_URL")
        self.ws = WebScraper(self.WS_URL)

        