
# Importing modules
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pymongo import *
from dotenv import load_dotenv
import certifi # import this module if having TLS certificate issues

import json
from bson.json_util import dumps
import operator

from os import getenv

# Importing queue module
from wa.queue import TimerQueue

# Importing order module
from wa.order import OrderType, Order

# Importing ws
from ws.webscraper import WebScraper

load_dotenv() # loading environment variables

DB_USERNAME = getenv('DB_USERNAME')
DB_PASSWORD = getenv('DB_PASSWORD')
DB_CLUSTER = getenv('DB_CLUSTER')
COLLECTION_NAME = getenv('COLLECTION_NAME')
SERVER_URL = getenv('SERVER_URL')
SERVER_PORT = getenv('SERVER_PORT')
WS_URL = getenv("WS_URL")
WS_USERNAME = getenv("WS_USERNAME")
WS_PASSWORD = getenv("WS_PASSWORD")


# Database config
client = MongoClient(f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@{DB_CLUSTER}/?retryWrites=true&w=majority", tlsCAFile=certifi.where())
db = client[COLLECTION_NAME]

# Setting up the server
app = FastAPI()
# Configuring web server for CORS
origins = [
"http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Web scraper config
# ws = WebScraper(WS_URL)
# ws.login(WS_USERNAME, WS_PASSWORD)

# Returns serealized JSON from db
def find_by_collection(collection_name): # returns all the elements in selected collection
    items = []
    for item in db[collection_name].find():
        items.append(item)
    return items

def response(items):
    return JSONResponse(content=json.loads(dumps(items)))

# Queues utils
def create_queues() -> list:
    table_list = find_by_collection("tables")
    queues = []
    table_list.sort(key=operator.itemgetter('number')) # sort the table list by ID
    for table in table_list:
        # i-th table -> (i-1)-th queue
        # queues.append(TimerQueue(table["number"], 5, table["count"]*MAX_DISHES)) # setting the max count of the queues based on the number of people
        queues.append(TimerQueue(id=table["number"], delay=20, size=3)) # setting the max count of the queues based on the number of people
    return queues

def print_queues():
    for queue in queues:
        print(queue)

def enqueue_order(table, dishes, background_tasks):
    queue = queues[table-1]
    first_time = queue.empty() # checking if it's the first time you're enqueuing
    if not queue.full():
        print_queues()
        try: # handling exception in case of ws failure
            queue.put(Order(table, dishes)) # insert order in the correct queue
            if first_time:
                print("[🏀] EMPTY: Queue is empty")
                # If it is the first order inserted in the queue, then start the timer
                background_tasks.add_task(queue.start_timer)
            elif queue.full(): # check if the newly inserted order fullfills the queue
                print("[💡] FULL: Queue is full")
                # 1. Dequeue dell'ordine
                while not queue.empty():
                    queue.get() # !PLACEHOLDER: REPLACE WITH THE NEXT LINE
                    # background_tasks.add_task(ws.process, queue, table, dishes) # 2. Print comanda
                    # ? BOH: queue.task_done() # mark the task as done
                queue.cancel_timer() # 3. Reset del timer
            else:
                print("[⏳] SEMI-FULL: Queue contains some elements")
                # Restart the timer
                queue.cancel_timer()
                background_tasks.add_task(queue.start_timer)
                pass
        except Exception as exception:
            print(f"\n[❌] Something went wrong: {exception}")
    else:
        enqueue_order(table, dishes, background_tasks)
        print("[💡] Queue is full")

def dequeue_order(queue, table):
    if not queue.empty():
        queue.get()

# Configuring the queues for processing orders
MAX_DISHES = int(getenv('MAX_DISHES'))
queues = create_queues()

# @GET requests
@app.get("/")
async def dishes():
    return response(find_by_collection("dishes"))

@app.get("/drinks")
def drinks():
    return response(find_by_collection("drinks"))
    
@app.get("/beers")
def beers():
    return response(find_by_collection("beers"))

@app.get("/desserts")
def desserts():
    return response(find_by_collection("desserts"))

@app.get("/wines")
def wines():
    return response(find_by_collection("wines"))

@app.get("/tables")
def tables():
    return response(find_by_collection("tables"))

@app.get("/menu")
async def menu():
    db_collection = db["menu"]

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

    return response(obj)
    
# @POST requests
@app.post("/order")
def order(order: OrderType, background_tasks: BackgroundTasks):
    try: # handling exception in case of ws failure
        enqueue_order(order.table, order.dishes, background_tasks) # enqueuing the newly received order in the queue
        return response({"status": "success", "statusCode": 201})
    except Exception as exception:
        print(f"\n[❌] Something went wrong: {exception}")
        return response({"status": "failure", "statusCode": 400})
            
