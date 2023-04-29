
# Importing modules
from flask import Flask, request
from flask_cors import CORS, cross_origin
from celery import Celery, Task, shared_task # for running complex tasks in background
import asyncio
from pymongo import *
from dotenv import load_dotenv
import certifi # import this module if having TLS certificate issues

import json
from bson.json_util import dumps

from os import getenv

# Importing queue module
from queue import Queue
# Importint timer module
from wa.timer import Timer

# Importing order module
from wa.order import Order

# Importing ws
from ws.webscraper import WebScraper

class Server:
    def __init__(self) -> None:
        # Config server settings
        self.config()

    def find_by_collection(self, collection_name) -> list: # returns all the elements in selected collection
        items = []
        for item in self.db[collection_name].find():
            items.append(item)
        return dumps(items) # convert to JSON format

    def run(self):
        # @GET requests
        @self.app.route("/")
        @cross_origin()
        def dishes():
            return self.find_by_collection("dishes")
        
        @self.app.route("/drinks")
        @cross_origin()
        def drinks():
            return self.find_by_collection("drinks")
            
        @self.app.route("/beers")
        @cross_origin()
        def beers():
            return self.find_by_collection("beers")
        
        @self.app.route("/desserts")
        @cross_origin()
        def desserts():
            return self.find_by_collection("desserts")
        
        @self.app.route("/wines")
        @cross_origin()
        def wines():
            return self.find_by_collection("wines")
        
        @self.app.route("/tables")
        @cross_origin()
        def tables():
            return self.find_by_collection("tables")

        @self.app.route("/menu")
        @cross_origin()
        def menu():
            db_collection = self.db["menu"]

            collections = [
                {
                    "title": "desserts",
                    "sections": []
                },
                {
                    "title": "dishes",
                    "sections": ["antipasti", "bowl", "degustazione", "frittura",
                "futomaki", "gunkan", "gyoza", "hanami special roll",
                "hosomaki", "insalate", "maki fritto", "menu cena",
                "nigiri", "onigiri", "primi", "riso", "sushi misto",
                "tartare e sashimi", "tataki", "temaki", "teppanyaki",
                "uramaki", "zuppe", "sushi gio"]
                },
                {
                    "title": "drinks",
                    "sections": []
                },
                {
                    "title": "wines",
                    "sections": ["bianchi", "bollicine", "rosati", "rossi"]
                }
            ]

            obj = {}
            
            for collection in collections:
                title, sections = collection.values()
                
                section_obj = {}
                for section in sections:
                    item = db_collection.aggregate([
                        { "$lookup": {
                            "from": title,
                            "localField": f"{title}.{section}", # Works with an array
                            # "pipeline": [{
                            #     "$sort": { "dish": 1 },
                            # }],
                            "foreignField": "_id",
                            "as": "menu" },
                        },
                    ])
                    section_obj[section] = json.loads(dumps(item))[0]["menu"]

                obj[title] = section_obj

            return dumps(obj)
        
        # @POST requests
        @self.app.route("/order", methods=["POST"])
        @cross_origin()
        def order():
            if request.method == "POST":
                try: # handling exception in case of ws failure
                    json_data = request.get_json()["data"] # json_data = {"table": 3, "dishes": [{"dish": "1", "qty": 1}]}
                    table, dishes = json_data.values() # getting the data from json
                    self.enqueue_order(table, dishes) # enqueuing the newly received order in the queue

                    self.print_queues()

                    # self.ws.login("a", "a")
                    # self.ws.process(json_content['data']) # processing the order: table=3, dish="001", qty=3
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

        # Setting up the server
        self.init_app()

        # Configuring the queues for processing orders
        self.MAX_DISHES = int(getenv('MAX_DISHES'))
        self.create_queues()

        # Web scraper config
        # self.WS_URL = getenv("WS_URL")
        # self.ws = WebScraper(self.WS_URL)

    # Creating the app
    def init_app(self) -> None:
        # Web server with flask
        self.PORT = getenv('PORT')
        self.app = Flask(__name__)

        # Setting celery app
        self.app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost",
            result_backend="redis://localhost",
            task_ignore_result=True,
            ),
        )
        self.celery_app = self.celery_init_app(self.app)

    # Celery app
    def celery_init_app(app: Flask) -> Celery:
        class FlaskTask(Task):
            def __call__(self, *args: object, **kwargs: object) -> object:
                with app.app_context():
                    return self.run(*args, **kwargs)
                
        celery_app = Celery(app.name, task_cls=FlaskTask)
        celery_app.config_from_object(app.config["CELERY"])
        celery_app.set_default()
        app.extensions["celery"] = celery_app
        return celery_app


    # Queues utils
    def create_queues(self):
        table_list = json.loads(self.find_by_collection("tables"))
        self.queues = []
        for table in table_list:
            # i-th table -> (i-1)-th queue
            self.queues.append(Queue(table["count"]*self.MAX_DISHES)) # setting the max count of the queues based on the number of people

    def enqueue_order(self, table, dishes):
        q = self.queues[table-1]
        first_time = q.empty() # checking if it's the first time you're enqueuing
        if not q.full():
            q.put(Order(table, dishes)) # insert order in the correct queue
            if first_time:
                # Start the timer
                result = self.start_timer.delay()
                print(result)
                pass
            elif q.full():
                # Dequeue dell'ordine, reset del timer, print comanda
                pass
            else:
                # Restart the timer
                pass
        else:
            print("[💡] Queue is full")

    def print_queue(self, q):
        print("[ ", end=' ')
        for q_item in q.queue:
            print(q_item, end=' <- ')
        print(" ]")

    def print_queues(self):
        for q in self.queues:
            self.print_queue(q)

    # Timer utils
    @shared_task(ignore_result=False)
    def start_timer(self):
        asyncio.sleep(2)
        return {"msg": "success"}
