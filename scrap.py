import requests
from bs4 import BeautifulSoup
import json
import csv
import os

MainUrl = "https://web.archive.org/web/20140901091007/http://catalog.uoregon.edu/arts_sciences/"
baseUrl = "https://web.archive.org"
grade_data = os.path.join(os.path.dirname(__file__), "gradedata.js")
output = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output, exist_ok=True)


"""
Extract the faculty names

When replacing the system data, ideally, discrepancies between names found in
“gradedata.js” and the names found in the scraped instructor data would be easy to resolve
using the administrator tools, to ensure that the data in your tables is clean, consistent and
accurate. (Optionally, as the two sources of data are brought into alignment, the tools could
generate statistics such as lists of names from both data sources that have yet to find a match,
so you can see how your data resolving process needs to be further improved.)
"""

# Send a GET request to the webpage

def get_catalog(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Could not load the main page. {response.status_code}")
    soup = BeautifulSoup(response.content, "html.parser")
    catalogs = [a["href"] for a in soup.find_all("a", href=True) if "arts_sciences/" in a["href"]]

    links = [baseUrl + link for link in catalogs]

    return links

catalog_links = get_catalog(MainUrl)

for link in catalog_links:
    print(link)


