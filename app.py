import requests
import re
import json
import time
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
from data_loader import DataLoader
from scrap import run_scraper
from config import Config


# Init flask app and configure MongoDB connection
app = Flask(__name__)
app.config.from_object(Config)
mongo = PyMongo(app)


# All the departments
NATURAL_SCIENCES_DEPARTMENTS = {
    "BI": "Biology", 
    "CH": "Chemistry", 
    "CIS": "Computer and Information Science",
    "GEOL": "Earth Science", 
    "GEN SCI": "General Science Program", 
    "HPHY": "Human Physiology",
    "MATH": "Mathematics", 
    "NEURO": "Neuroscience", 
    "PHYS": "Physics", 
    "PSY": "Psychology"
}

# Init the data processor with the database and departments 
data_processor = DataLoader(mongo.db, NATURAL_SCIENCES_DEPARTMENTS)

# Admin page
@app.route("/admin")
def admin_page():
    return render_template("admin_page.html")


# User page, handles requests to display course info
@app.route("/user")
def user_page():
    try:
        # Grab course and instructor names from the database
        courses_in_database = mongo.db.grades.distinct("course")
        instructors_in_database = mongo.db.grades.distinct("instructor")
        print("Courses in database:", courses_in_database)
        print("Instructors in database:", instructors_in_database)  

        # Format and extracts instructor, departments and classe, funcs from data_loader.py
        cleaned_instructor_names = data_processor.clean_instructor_names(instructors_in_database)
        department_options, class_options = data_processor.extract_departments_and_classes(courses_in_database)

        selected_department = request.args.get("department", "")
        selected_class = request.args.get("class", "")
        selected_instructor = request.args.get("teacher", "")
        
        # Build query based on requests and find the matching results 
        query = build_course_query(selected_department, selected_class, selected_instructor)
        results = list(mongo.db.grades.find(query).limit(100))

        return render_template(
            "user_page.html",
            departments=department_options,
            classes=class_options,
            teachers=sorted(cleaned_instructor_names),
            results=results,
            request=request
        )
    
    except Exception as e:
        return f"User Page Error: {e}", 500
    


# Load js data, extract the JSON and insert it into the database
@app.route("/load_remote_js", methods=["POST"])
def load_remote_js():
    try:
        # Get the file URL from user input on admin page
        file_url = request.form.get("file_url")
        if not file_url or not file_url.startswith("http"):
            flash("Invalid file URL provided.", "danger")
            return redirect(url_for("admin_page"))
        
        response = requests.get(file_url, timeout=10)
        response.raise_for_status()
        content = response.text.strip()

        # Grab the JSON data 
        match = re.search(r'var\s+groups\s*=\s*({.*?});', content, re.DOTALL)
        if not match:
            flash("Could not extract JSON data from the remote file.", "danger")
            return redirect(url_for("admin_page"))

        # Format the JSON data for the database
        groups = json.loads(match.group(1))
        records = data_processor.transform_course_data(groups)

        # Clear existing data dn insert new data into records 
        if records:
            mongo.db.grades.delete_many({})
            mongo.db.grades.insert_many(records)
            flash(f"Database successfully populated with {len(records)} records!", "success")
        else:
            flash("No valid data to insert.", "warning")

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    time.sleep(3)
    return redirect(url_for("admin_page"))


# Scrape faculty data and insert/update it in the database
@app.route("/scrape_faculty", methods=["POST"])
def scrape_faculty():
    try:
        # Run the scraper to get faculty data then insert to db
        faculty_data = run_scraper()
        print("Scraped Data:", faculty_data)  

        data_processor.insert_faculty_data(faculty_data)

    except Exception as e:
        flash(f"An error occurred during faculty scraping: {e}", "danger")

    return redirect(url_for("admin_page"))


# Clears database of all records from the grades and faculty collections
@app.route("/clear_database", methods=["POST"])
def clear_database():
    data_processor.clear_all_collections()
    return redirect(url_for("admin_page"))


# Build mongodb query based on the selected filters
def build_course_query(department, course_class, instructor):
    query = {}
    if department:
        query["course"] = {'$regex': f'^{department}'}
    if course_class:
        query["course"] = {'$regex': f'{course_class}$'}
    if instructor:
        query["instructor"] = instructor
    return query


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
