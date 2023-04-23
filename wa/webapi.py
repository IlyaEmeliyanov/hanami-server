
# Importing modules
from flask import Flask, request
from flask_cors import CORS, cross_origin
from pymongo import *
from dotenv import load_dotenv
import certifi # import this module if having TLS certificate issues

import json
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
        @cross_origin()
        def dishes():
            collection = self.db["dishes"]
            obj = []
            for item in collection.find():
                obj.append(item)
            return dumps(obj)
        
        @self.app.route("/drinks")
        @cross_origin()
        def drinks():
            collection = self.db["drinks"]
            obj = []
            for item in collection.find():
                obj.append(item)
            return dumps(obj)
            
        @self.app.route("/beers")
        @cross_origin()
        def beers():
            collection = self.db["beers"]
            obj = []
            for item in collection.find():
                obj.append(item)
            return dumps(obj)
        
        @self.app.route("/desserts")
        @cross_origin()
        def desserts():
            collection = self.db["desserts"]
            obj = []
            for item in collection.find():
                obj.append(item)
            return dumps(obj)

        @self.app.route("/menu")
        @cross_origin()
        def menu():
            collection = self.db["menu"]
            categories = [
                "antipasti", "bowl", "degustazione", "frittura",
                "futomaki", "gunkan", "gyoza", "hanami special roll",
                "hosomaki", "insalate", "maki fritto", "menu cena",
                "nigiri", "onigiri", "primi", "riso", "sushi misto",
                "tartare e sashimi", "tataki", "temaki", "teppanyaki",
                "uramaki", "zuppe", "sushi gio"
            ]
            obj = []
            
            for category in categories:
                item = collection.aggregate(
                [
                    { "$lookup": {
                        "from": "dishes",
                        "localField": f"dishes.{category}", # Works with an array
                        "pipeline": [{
                            "$sort": { "dish": 1 },
                        }],
                        "foreignField": "_id",
                        "as": "menu" },
                    },
                ])

                item_dict = json.loads(dumps(item))[0]["menu"]
                obj.append({category: item_dict})

            return dumps(obj)
        
        # @POST requests
        @self.app.route("/order", methods=["POST"])
        @cross_origin()
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
        # self.WS_URL = getenv("WS_URL")
        # self.ws = WebScraper(self.WS_URL)

        