# Project-1-EasyA

## Overview
EasyA is a web based application designed to help students analyze the grading history of courses and instructors. 
Students can use historical grade data to compare grading distributions and make informed decisions about which classes and instructors to choose.
You can find the classes that have the highest chance of giving you an A. This project was made for CS 422.

## Features

- **User Page:**
The user page allows students to interact with course and instructor data through drop-down menus to filter results. The user can filter by department, class, or instructor and view the relevant results. 
  
- **Admin Page:**  
The admin page allows the user to load, manage, and update course and faculty data. Data can be loaded by uploading remote JS data files or through a web scraper. The page also has options to clear the database and merge the data. localhost:5000/admin

- **Search classes:**
Search for classes, instructors, and departments using drop-down menus.

- **Grade Comparison:**
Compare grades of instructors or courses using processed JS datasets.

- **Data Loading and Management:**
Load course and faculty data from remote JS files or web scraping, stored in a MongoDB database.

- **Faculty Scraping:**
Extract and store faculty data in MongoDB database using web scraper.

- **Graph:**



## Installation and Setup

### Prerequisites
- **Docker:** Make sure Docker and Docker Compose are installed. You can follow these official instructions:
  - [Docker Installation](https://docs.docker.com/get-docker/)
  - [Docker Compose Installation](https://docs.docker.com/compose/install/)


1. **Clone the Repository:**  
   ```bash
   git clone https://github.com/your-repo/Project-1-EasyA.git
   cd Project-1-EasyA

2. **Build and Run the Containers:**
   - Run the following command to build the project and start the containers:
   Steps to set up the project using Docker and MongoDB.
   ```bash
   docker-compose up --build

3. **Access the Application:**
   - Open your browser and navigate to:
   ```bash
   http://localhost:5000/admin  -> Admin Page  
   http://localhost:5000/user   -> User Page  


## How to use
- Admin Page:
  - Load data either by specifying a remote JavaScript URL or by running the web scraper.
    - Web scrape URL: https://web.archive.org/web/20141107201343/http://catalog.uoregon.edu/arts_sciences/
    - JS URL: https://emeraldmediagroup.github.io/grade-data/gradedata.js
  - Clear and reload the database as needed.
 
- User Page:
  - Use the dropdown menus to select a department, instructor, and class, or 100-400 department level classes
  - Visualize grade distributions through bar charts 

## Contributors
- Karma Woeser
- Jason Webster
- Raj Gill
- Giovanni Mendoza Celestino

