import requests
from bs4 import BeautifulSoup

url = "https://web.archive.org/web/20140901091007/http://catalog.uoregon.edu/arts_sciences/"

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
response = requests.get(url)
if response.status_code == 200:
    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find and extract faculty names (modify the tag/class based on the actual structure)
    # For demonstration, assume names are in <li> under a specific class or section
    # faculty_list = soup.find_all('li')  # Adjust this to target the specific structure

    
    # Find all elements with the class "facultylist"
    faculty_elements = soup.find_all(class_="facultylist")
    
    # Process and print the faculty names
    for faculty in faculty_elements:
        name = faculty.get_text(strip=True)
        if name:
            print(name)

else:
    print(f"Failed to access the webpage. Status code: {response.status_code}")
