# EasyA – Grading Analysis App 

EasyA is a web based application designed to help students analyze the grading history of courses and instructors. 
Students can use historical grade data to compare grading distributions and make informed decisions about which classes and instructors to choose. This application makes it easy to find the classes that have the highest chance of giving you an A. Project was created for CS 422 at the University of Oregon.

## :zap: Features

**User Page:** The user page is designed for students to filter, compare, and visualize grade distributions interactively.  
  - **Dynamic Filtering Dropdowns:**  
    - Filter by department, class, or instructor. The available options update dynamically based on the user’s selections (e.g., selecting a department will filter the classes and instructors shown).  
    - Departments can be sorted by class levels (e.g., 100-level, 200-level, up to 400-level classes).  
  - **Grade Comparison Buttons:**  
    - The page allows users to toggle between viewing **A, B, C, D, or F** grade distributions using buttons that dynamically reload the graph.  
  - **Graph Visualization:**  
    - The grade data is displayed using **Chart.js** in a bar graph format for easy comparisons.
  
**Admin Page:** The admin page allows administrators to load historical grade data from a remote JavaScript file or scrape faculty information using predefined department URLs.
  - **Load Remote JS:**
    - Extracts course and instructor information from the provided JS data file and stores it in the **MongoDB** database.
  - **Faculty Scraper:**
    - Scrapes faculty names and department associations from archived department pages. 
  - **Database Management:**
    - There are options to clear or update current database records.


## :electric_plug: Installation and Setup

### Prerequisites
- **Docker:** Make sure Docker is installed. You can follow these official instructions:
  - Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop)

1. **Clone the Repository:**  
   ```bash
   git clone https://github.com/your-repo/Project-1-EasyA.git
   cd Project-1-EasyA

2. **Build and Run the Containers:**
   - Run the following command to build the project and start the containers:
   ```bash
   docker-compose up --build

3. **Access the Application:**
   - Open your browser and navigate to:
   ```bash
   http://localhost:5000/admin 
   http://localhost:5000/user 

## :rocket: How to use
- Admin Page:
  - Provides options to process and load grade data through Flask's backend routes.
    - JS URL:
      - https://emeraldmediagroup.github.io/grade-data/gradedata.js
    - Web scrape URL:
      - https://web.archive.org/web/20141107201343/http://catalog.uoregon.edu/arts_sciences/
  - Clear and reload the database when needed.
 
 - User Page:
    - Use the dropdown menus to filter department, instructor, or class to dynamically update graphs.
    - Use the grade buttons (A, B, C, D, or F) to switch between different grading distributions.
    - View bar graphs representing the percentage of selected grades.


##  :file_folder: File Structure
```
Project-1-EasyA/
│
├── app.py                 # Main flask application
├── data_loader.py         # Data processing and database management
├── config.py              # Configuration file
├── scrap.py               # Web scraper
├── dockerfile             # Docker setup
├── docker-compose.yml     # Docker compose configuration
├── docs/                  # Documents 
│   └── EasyA.pdf          # Final doc
│   └── SRS.pdf            # SRS doc
├── static/                # Static files 
│   └── gradedata.js       # Grade data 
├── templates/             # HTML templates for frontend
│   └── user_page.html     # User page
│   └── admin_page.html    # Admin page
├── tests/                 # Unit and integration tests
│   └── tests.py           # Tests for database
│   └── testing.txt        # Testing ideas
├── etc/                   # extra text files
│   └── ideas.txt          # Initial Ideas
│   └── requirements.txt   # Dependencies
│   └── suggustions.txt    # Suggestions
│   └── variables.txt      # database variables
├── README.md              # Project README
└── .gitignore             # Git ignore file
```


## :star2: Contributors
- Karma Woeser
- Jason Webster
- Raj Gill
- Giovanni Mendoza Celestino

