import requests
import json

#URL of gradedata.js file
url = "https://emeraldmediagroup.github.io/grade-data/gradedata.js"

try:
    response = requests.get(url) #get data from URL
    response.raise_for_status()  #raise error if unable to get data from URL
    raw_data = response.text.strip() #extract data and put it into raw_data

    if raw_data.startswith("var groups ="):#check if it starts with JSON
        start_index = raw_data.find("=") + 1  # Find where JSON starts and ends to isolate it. Starts after "="
        end_index = raw_data.rfind("};") + 1  # Ends at "}:"
        json_data = raw_data[start_index:end_index].strip()
    else:
        raise ValueError("The file does not start with 'var groups ='. Please inspect the content.")

    parsed_data = json.loads(json_data)#loads data in



except requests.RequestException as e:
    print(f"Error fetching the file: {e}")
except json.JSONDecodeError as e:
    print(f"Error parsing JSON data: {e}")
except ValueError as e:
    print(f"Error processing file content: {e}")
