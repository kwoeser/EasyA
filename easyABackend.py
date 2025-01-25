import os
import requests
import json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = os.getenv("MONGO_URI")

if not uri:
    raise ValueError("MongoDB connection string not found in environment variables.")

client = MongoClient(uri, server_api=ServerApi('1'))#connect to mongo

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(f"Connection error: {e}")

db = client["university_grades"]  #Database name for mongo
collection = db["grades"]         #Collection name for mongo

#URL of gradedata.js file
url = "https://emeraldmediagroup.github.io/grade-data/gradedata.js"

try:
    response = requests.get(url) #get data from URL
    response.raise_for_status()  #raise error if unable to get data from URL
    raw_data = response.text.strip() #extract data and put it into raw_data

    if raw_data.startswith("var groups ="):#check if it starts with JSON
        start_index = raw_data.find("=") + 1  #Find where JSON starts and ends to isolate it. Starts after "="
        end_index = raw_data.rfind("};") + 1  #Ends at "}:"
        json_data = raw_data[start_index:end_index].strip()
    else:
        raise ValueError("The file does not start with 'var groups ='. Please inspect the content.")

    parsed_data = json.loads(json_data)#loads data in

    if isinstance(parsed_data, list):
        collection.insert_many(parsed_data)#checks if data is multiple dictionaries
    elif isinstance(parsed_data, dict):
        collection.insert_one(parsed_data)#checks if data is only one dictionary
    else:
        raise ValueError("Unexpected data format.")

    print("Data successfully inserted into MongoDB.")


except requests.RequestException as e:
    print(f"Error fetching the file: {e}")
except json.JSONDecodeError as e:
    print(f"Error parsing JSON data: {e}")
except ValueError as e:
    print(f"Error processing file content: {e}")