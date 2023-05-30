
# Importing modules
from fastapi import FastAPI, BackgroundTasks, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pymongo import MongoClient
from dotenv import load_dotenv
import certifi # import this module if having TLS certificate issues

import json
from bson.json_util import dumps
import operator

from os import getenv

# Importing custom modules
from ws.webscraper import WebScraper
from wa.timer_queue import TimerQueue
from wa.order import OrderType, TimerType

class WebAPI:
    def __init__(self):
        load_dotenv()  # loading environment variables
        self.config()

    def config(self):
        DB_USERNAME = getenv('DB_USERNAME')
        DB_PASSWORD = getenv('DB_PASSWORD')
        DB_CLUSTER = getenv('DB_CLUSTER')
        COLLECTION_NAME = getenv('COLLECTION_NAME')

        # Database config
        # client = MongoClient("localhost", 27017)
        # self.db = client["hanami"]
        client = MongoClient(f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@{DB_CLUSTER}/?retryWrites=true&w=majority",
                             tlsCAFile=certifi.where())
        self.db = client[COLLECTION_NAME]

        self.SERVER_URL = getenv('SERVER_URL')
        self.SERVER_PORT = getenv('SERVER_PORT')

        self.router = APIRouter()
        routes = [
            {"pathname": "dishes", "method": self.get_items_by_collection, "request_type": "GET"},
            {"pathname": "drinks", "method": self.get_items_by_collection, "request_type": "GET"},
            {"pathname": "beers", "method": self.get_items_by_collection, "request_type": "GET"},
            {"pathname": "desserts", "method": self.get_items_by_collection, "request_type": "GET"},
            {"pathname": "wines", "method": self.get_items_by_collection, "request_type": "GET"},
            {"pathname": "tables", "method": self.get_items_by_collection, "request_type": "GET"},
            {"pathname": "menu", "method": self.get_menu, "request_type": "GET"},
            {"pathname": "timer", "method": self.get_timer, "request_type": "POST"},
            {"pathname": "order", "method": self.post_order, "request_type": "POST"}
        ]
        for route in routes:
            pathname = route["pathname"]
            method = route["method"]
            request_type = route["request_type"]
            self.router.add_api_route(f"/{pathname}", method, methods=[request_type])

        self.WS_URL = getenv("WS_URL")
        self.WS_USERNAME = getenv("WS_USERNAME")
        self.WS_PASSWORD = getenv("WS_PASSWORD")

        # Web scraper config
        self.ws = WebScraper(self.WS_URL)
        self.ws.login(self.WS_USERNAME, self.WS_PASSWORD)

        # Queues config | queues are used to control the orders
        self.MAX_DISHES = int(getenv('MAX_DISHES'))
        self.queues = self.create_queues()

    # @GET requests
    async def get_items_by_collection(self, request: Request):
        collection_name = request.url._url.split("/")[-1]
        return self.response(self.find_by_collection(collection_name))

    async def get_menu(self):
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
            },
            {
                "title": "beers",
                "sections": []
            }
        ]

        obj = {}

        for collection in collections:
            title, sections = collection.values()

            section_obj = {}
            if sections == []:
                section_obj = db_collection.aggregate([
                    {"$lookup": {
                        "from": title,
                        "localField": f"{title}",  # Works with an array
                        "foreignField": "_id",
                        "as": "menu"},
                    },
                ])
                section_obj = json.loads(dumps(section_obj))[0]["menu"]

            for section in sections:
                item = db_collection.aggregate([
                    {"$lookup": {
                        "from": title,
                        "localField": f"{title}.{section}",  # Works with an array
                        # "pipeline": [{
                        #     "$sort": { "dish": 1 },
                        # }],
                        "foreignField": "_id",
                        "as": "menu"},
                    },
                ])
                section_obj[section] = json.loads(dumps(item))[0]["menu"]

            obj[title] = section_obj

        return self.response(obj)

    # @POST requests
    # @POST request
    # body: { "table": "<table_number>", dishes: [{"dish": <dish_number>, "quantity": <dish_quantity>} ...] }
    # Description: enqueues the order in the corresponding queue
    async def post_order(self, order: OrderType, background_tasks: BackgroundTasks):
        try:  # handling exception in case of ws failure
            # Find the corresponding queue
            queue = None
            for q in self.queues:
                if q.table_number == order.table: queue = q
            queue.enqueue_order(order, background_tasks)  # enqueuing the newly received order in the queue
            return self.response({"status": "success", "statusCode": 201})
        except Exception as exception:
            print(f"\n[ERROR] Something went wrong in post_order: {exception}")
            return self.response({"status": "failure", "statusCode": 400})

    # @POST request
    # body: { "table": "<table_number>" }
    # Description: requests the current counter of the timer from a specific queue
    async def get_timer(self, timer: TimerType):
        # Find the corresponding queue
        queue = None
        for q in self.queues:
            if q.table_number == timer.table: queue = q
        print(queue)
        queue_counter = queue.get_cur_time()
        return self.response({"status": "success", "statusCode": 200, "counter": queue_counter})

    # @UTIL functions
    # Returns serialized JSON from db
    def find_by_collection(self, collection_name):  # returns all the elements in selected collection
        items = []
        for item in self.db[collection_name].find():
            items.append(item)
        return items


    def response(self, items):
        return JSONResponse(content=json.loads(dumps(items)))


    # Queues utils
    def create_queues(self) -> list:
        table_list = self.find_by_collection("tables")
        queues = []
        table_list.sort(key=operator.itemgetter('number'))  # sort the table list by ID
        for i, table in enumerate(table_list):
            # Append each queue to the array of queues
            queues.append(TimerQueue(id=i, table_number=table["number"], delay=10, size=3, ws=self.ws)) # setting the max count of the queues based on the number of people
        return queues


# Setting up the server
app = FastAPI()
server = WebAPI()
app.include_router(server.router)

# Configuring CORS for access from other endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
