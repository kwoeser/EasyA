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


NATURAL_SCIENCES_DEPARTMENTS = {
    "ANTH": "Anthropology",
    "BI": "Biology",
    "CH": "Chemistry",
    "CH": "Biochemistry",
    "CIS": "Computer and Information Science",
    "ES": "Earth Science",
    "GEN SCI": "General Science Program",
    "GEOG": "Geography",
    "GEOL": "Geological",
    "HPHY": "Human Physiology",
    "MATH": "Mathematics",
    "NEURO": "Neuroscience",
    "PHYS": "Physics",
    "PSY": "Psychology"
}


# Init the data processor with the database and departments 
data_processor = DataLoader(mongo.db, NATURAL_SCIENCES_DEPARTMENTS)


# Merge Data Route
@app.route("/merge_data", methods=["POST"])
def merge_data():
    try:
        data_processor.merge_faculty_with_grades()
        flash("Faculty data successfully merged with grade records.", "success")
    except Exception as e:
        flash(f"An error occurred during data merging: {e}", "danger")

    return redirect(url_for("admin_page"))

#Trying to process grade data in the dropdown choices and narrow 
#functionality of the user_page
@app.before_request
def create_indexes():
    if not hasattr(app, 'indexes_created'):
        mongo.db.grades.create_index("course")
        mongo.db.grades.create_index("instructor")
        mongo.db.grades.create_index([("course", 1), ("instructor", 1)])  # Compound index
        mongo.db.grades.create_index("department")
        app.indexes_created = True  # Ensure it's only done once
        print("Indexes created successfully.")


# Admin page
@app.route("/admin")
def admin_page():
    return render_template("admin_page.html")

# User page
@app.route("/user")
def user_page():
    try:
        department = request.args.get("department", "")
        single_class = request.args.get("class", "")
        instructor_type = request.args.get("faculty_type", "all")
        grade_view = request.args.get("grade_view", "easyA")

        query = {}
        if department:
            query["course"] = {"$regex": f"^{department}"}
        if single_class:
            query["course"] = single_class

        natural_sciences_abbrevs = NATURAL_SCIENCES_DEPARTMENTS.keys()

        natural_science_classes = mongo.db.grades.distinct(
            "course", {"course": {"$regex": f"^({'|'.join(natural_sciences_abbrevs)})"}}
        )
        natural_science_teachers = mongo.db.grades.distinct(
            "instructor", {"course": {"$regex": f"^({'|'.join(natural_sciences_abbrevs)})"}}
        )

        # Build mappings
        teacher_department_map = {
            doc.get("instructor", "Unknown"): doc.get("department", "Unknown")
            for doc in mongo.db.faculty.find({}, {"instructor": 1, "department": 1})
        }

        teacher_classes_map = {
            teacher: list(mongo.db.grades.distinct("course", {"instructor": teacher}))
            for teacher in natural_science_teachers
        }

        class_department_map = {
            course: course[:4]  # Assuming first 4 chars represent department (e.g., CIS101)
            for course in natural_science_classes
        }

        class_teachers_map = {
            course: list(mongo.db.grades.distinct("instructor", {"course": course}))
            for course in natural_science_classes
        }

        # Graph Data
        results = list(mongo.db.grades.find(query))
        data_by_instructor = {}
        for r in results:
            instructor = r.get("instructor", "Unknown")  
            data_by_instructor.setdefault(instructor, {"count": 0, "sum": 0.0})

            if grade_view == "easyA":
                data_by_instructor[instructor]["sum"] += r.get("aprec", 0.0)
            else:
                data_by_instructor[instructor]["sum"] += r.get("dprec", 0.0) + r.get("fprec", 0.0)

            data_by_instructor[instructor]["count"] += 1

        graph_data = [
            {"instructor": instructor, "value": info["sum"] / info["count"]}
            for instructor, info in data_by_instructor.items()
        ]

        graph_data.sort(key=lambda x: x["value"], reverse=True)

        return render_template(
            "user_page.html",
            graph_data=graph_data if request.args else [],
            departments=NATURAL_SCIENCES_DEPARTMENTS.keys(),
            teachers=natural_science_teachers,
            classes=natural_science_classes,
            teacher_department_map=teacher_department_map,
            teacher_classes_map=teacher_classes_map,
            class_department_map=class_department_map,
            class_teachers_map=class_teachers_map,
        )

    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500






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


# Helper function to build MongoDB queries
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