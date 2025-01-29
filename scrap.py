import requests
from bs4 import BeautifulSoup
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

MainUrl = "https://web.archive.org/web/20140901091007/http://catalog.uoregon.edu/arts_sciences/"
baseUrl = "https://web.archive.org"
output = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output, exist_ok=True)

def requests_retry_session(retries=5, backoff_factor=2):
    session = requests.Session()
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

session = requests_retry_session()

def save_faculty_data(faculty):
    with open("faculty_data.json", "w") as file:
        json.dump(faculty, file, indent=4)

def get_catalog(url):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        catalogs = [a["href"] for a in soup.find_all("a", href=True) if "arts_sciences/" in a["href"]]
        links = [link if link.startswith("http") else baseUrl + link for link in catalogs]
        return links
    except Exception as e:
        print(f"Could not get catalog links: {e}")
        return []

def get_faculty(url):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        namesPTags = soup.find_all("p", class_="facultylist")
        return [p.get_text(strip=True) for p in namesPTags]
    except Exception as e:
        print(f"Could not to get the faculty for {url}: {e}")
        return []

def scrape_faculty(catalog_links):
    faculty = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_link = {executor.submit(get_faculty, link): link for link in catalog_links}
        for future in as_completed(future_to_link):
            link = future_to_link[future]
            try:
                faculty[link] = future.result()
            except Exception as e:
                print(f"Error processing {link}: {e}")
    return faculty

if __name__ == "__main__":
    catalog_links = get_catalog(MainUrl)
    print(f"Found {len(catalog_links)} links.")
    faculty_data = scrape_faculty(catalog_links)
    save_faculty_data(faculty_data)
    print("Scraping complete and saved to 'faculty_data.json'.")
