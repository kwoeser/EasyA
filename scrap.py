import requests
from bs4 import BeautifulSoup
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Define Main URL and Base URL for Web Archive
MainUrl = "https://web.archive.org/web/20140901091007/http://catalog.uoregon.edu/arts_sciences/"
baseUrl = "https://web.archive.org"

# Output directory setup
output = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output, exist_ok=True)

# List of Natural Sciences Departments we want to scrape
NATURAL_SCIENCES_DEPARTMENTS = [
    ("CH", "Chemistry"),
    ("CH", "Biochemistry"),
    ("ANTH", "Anthropology"),
    ("BI", "Biology"),
    ("CIS", "Computer and Information Science"),
    ("ES", "Earth Science"),
    ("GEN SCI", "General Science Program"),
    ("GEOG", "Geography"),
    ("GEOL", "Geological"),
    ("HPHY", "Human Physiology"),
    ("MATH", "Mathematics"),
    ("NEURO", "Neuroscience"),
    ("PHYS", "Physics"),
    ("PSY", "Psychology")
]

# Retry Session for Handling Request Failures
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

# Function to format names as "Last, First Middle"
def format_name(name):
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[-1]}, {' '.join(parts[:-1])}"
    return name  # Return as-is if it's a single name

# Get department catalog links and filter only natural sciences
def get_catalog(url):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Find department links
        catalogs = [a["href"] for a in soup.find_all("a", href=True) if "arts_sciences/" in a["href"]]
        links = [link if link.startswith("http") else baseUrl + link for link in catalogs]

        # Filter to include only Natural Sciences departments
        filtered_links = {}
        for link in links:
            for dept_code, dept_name in NATURAL_SCIENCES_DEPARTMENTS:
                if dept_code.replace(" ", "").lower() in link.replace(" ", "").lower():
                    filtered_links[link] = dept_code
                    break

        return filtered_links
    except Exception as e:
        print(f"Could not get catalog links: {e}")
        return {}

# Extract faculty names from a department page
def get_faculty(url, department_code):
    try:
        print(f"📡 Fetching: {url}")
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract Faculty Names
        faculty_names = set()
        faculty_pattern = re.compile(r"([A-Z][a-zA-Z\-\.\s]+),\s*(professor|assistant professor|associate professor|lecturer|instructor)", re.IGNORECASE)
        for p in soup.find_all("p"):
            matches = faculty_pattern.findall(p.get_text())
            for match in matches:
                formatted_name = format_name(match[0].strip())
                faculty_names.add(formatted_name)

        if not faculty_names:
            print(f"⚠️ No faculty found in {url}, skipping department.")
            return []

        faculty_data = [{"name": name, "department": department_code} for name in faculty_names]

        print(f"✅ Extracted {len(faculty_names)} faculty members from {url}")
        return faculty_data

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return []

# Scrape faculty data from filtered catalog links
def scrape_faculty(catalog_links):
    faculty = []
    processed_departments = set()

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_link = {}

        for link, dept_code in catalog_links.items():
            if dept_code in processed_departments:
                print(f"⚠️ Skipping duplicate scraping of {dept_code}")
                continue
            processed_departments.add(dept_code)
            future_to_link[executor.submit(get_faculty, link, dept_code)] = link

        for future in as_completed(future_to_link):
            try:
                faculty.extend(future.result())
            except Exception as e:
                print(f"❌ Error processing {future_to_link[future]}: {e}")

    return faculty

# Main function to scrape faculty data
def run_scraper():
    print("🕵️ Starting Scraper...")
    catalog_links = get_catalog(MainUrl)
    print(f"✅ Found {len(catalog_links)} relevant department links.")

    if not catalog_links:
        print("❌ No catalog links found! Check if the website structure has changed.")
        return []

    faculty_data = scrape_faculty(catalog_links)
    print(f"📌 Scraped {len(faculty_data)} faculty entries.")

    if not faculty_data:
        print("⚠️ No faculty data was collected. Something might be wrong.")
    else:
        print(f"🎯 Successfully collected {len(faculty_data)} faculty records.")

    return faculty_data

# Flask integration
def scraper_api():
    data = run_scraper()
    with open("faculty_data.json", "w") as file:
        json.dump(data, file, indent=4)
    return {"status": "success", "message": f"Scraped {len(data)} faculty records."}

if __name__ == "__main__":
    scraper_api()
