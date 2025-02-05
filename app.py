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
    """
    Merges faculty data with grade records in MongoDB.
    """
    try:
        data_processor.merge_faculty_with_grades()
        flash("Faculty data successfully merged with grade records.", "success")
    except Exception as e:
        flash(f"An error occurred during data merging: {e}", "danger")

    return redirect(url_for("admin_page"))

# Trying to process grade data in the dropdown choices and narrow 
# functionality of the user_page
@app.before_request
def create_indexes():
    """
    Creates necessary MongoDB indexes for query performance.
    """
    if not hasattr(app, 'indexes_created'):
        mongo.db.grades.create_index("course")
        mongo.db.grades.create_index("instructor")
        mongo.db.grades.create_index([("course", 1), ("instructor", 1)])  # Compound index
        mongo.db.faculty.create_index("department")  # Add index for faculty department
        mongo.db.faculty.create_index("instructor")  # Add index for instructor name
        app.indexes_created = True
        print("Indexes created successfully.")


# Admin page
@app.route("/admin")
def admin_page():
    """
    Renders the admin page for data handling
    """
    return render_template("admin_page.html")


# User page
@app.route("/user")
def user_page():
    """
    Render the user page. Displays course and grade data based on 
    user-selected filters such as department, class, and instructor.
    """
    try:
        department = request.args.get("department", "")
        single_class = request.args.get("class", "")
        instructor_type = request.args.get("faculty_type", "all")
        grade_view = request.args.get("grade_view", "easyA")
        selected_teacher = request.args.get("teacher", "")
        selected_level = request.args.get("level", "")  # Capture selected level

        # Auto-select department based on the selected teacher if not already chosen
        if selected_teacher and not department:
            teacher_dept = mongo.db.faculty.find_one({"instructor": selected_teacher}, {"department": 1})
            if teacher_dept:
                department = teacher_dept.get("department", "")

        query = {}
        if selected_level:
            # Handle Level Filtering
            dept_abbr, level_prefix = selected_level.split("-")
            query["course"] = {"$regex": f"^{dept_abbr}{level_prefix[0]}"}
        elif department:
            query["course"] = {"$regex": f"^{department}"}

        if single_class:
            query["course"] = single_class
        if selected_teacher:
            query["instructor"] = selected_teacher

        natural_sciences_abbrevs = NATURAL_SCIENCES_DEPARTMENTS.keys()

        natural_science_classes = mongo.db.grades.distinct(
            "course", {"course": {"$regex": f"^({'|'.join(natural_sciences_abbrevs)})"}}
        )
        natural_science_teachers = mongo.db.faculty.distinct("name")

        # Build mappings
        teacher_department_map = {}
        for doc in mongo.db.faculty.find({}, {"name": 1, "department": 1}):
            instructor_name = doc.get("name", "Unknown")
            department = doc.get("department", "Unknown")
            teacher_department_map[instructor_name] = department

        teacher_classes_map = {
            teacher: ';'.join(str(course) for course in mongo.db.grades.distinct("course", {"instructor": teacher}))
            for teacher in natural_science_teachers
        }

        class_department_map = {
            # Extracts CIS, BI, CH, etc.
            course: re.match(r'^[A-Z]+', course).group()  
            for course in natural_science_classes
        }

        class_teachers_map = {
            course: ';'.join(mongo.db.grades.distinct("instructor", {"course": course}))
            for course in natural_science_classes
        }

        # Graph Data
        results = list(mongo.db.grades.find(query))

        if selected_level:
            # Group data by Class when Level is selected
            data_by_class = {}
            for r in results:
                course = r.get("course", "Unknown")
                data_by_class.setdefault(course, {"count": 0, "sum": 0.0, "aprec": 0.0, "bprec": 0.0, "cprec": 0.0, "dprec": 0.0, "fprec": 0.0})

                data_by_class[course]["aprec"] += r.get("aprec", 0.0)
                data_by_class[course]["bprec"] += r.get("bprec", 0.0)
                data_by_class[course]["cprec"] += r.get("cprec", 0.0)
                data_by_class[course]["dprec"] += r.get("dprec", 0.0)
                data_by_class[course]["fprec"] += r.get("fprec", 0.0)

                data_by_class[course]["count"] += 1

            graph_data = [
                {
                    "label": course,
                    "aprec": info["aprec"] / info["count"],
                    "bprec": info["bprec"] / info["count"],
                    "cprec": info["cprec"] / info["count"],
                    "dprec": info["dprec"] / info["count"],
                    "fprec": info["fprec"] / info["count"],
                }
                for course, info in data_by_class.items()
            ]

        else:
            # Default: Group data by Instructor
            data_by_instructor = {}
            for r in results:
                instructor = r.get("instructor", "Unknown")
                data_by_instructor.setdefault(instructor, {"count": 0, "aprec": 0.0, "bprec": 0.0, "cprec": 0.0, "dprec": 0.0, "fprec": 0.0})

                data_by_instructor[instructor]["aprec"] += r.get("aprec", 0.0)
                data_by_instructor[instructor]["bprec"] += r.get("bprec", 0.0)
                data_by_instructor[instructor]["cprec"] += r.get("cprec", 0.0)
                data_by_instructor[instructor]["dprec"] += r.get("dprec", 0.0)
                data_by_instructor[instructor]["fprec"] += r.get("fprec", 0.0)

                data_by_instructor[instructor]["count"] += 1

            graph_data = [
                {
                    "label": instructor,
                    "aprec": info["aprec"] / info["count"],
                    "bprec": info["bprec"] / info["count"],
                    "cprec": info["cprec"] / info["count"],
                    "dprec": info["dprec"] / info["count"],
                    "fprec": info["fprec"] / info["count"],
                }
                for instructor, info in data_by_instructor.items()
            ]

        # Sort based on the selected grade (default to A)
        selected_grade = request.args.get("grade", "A").lower() + "prec"
        graph_data.sort(key=lambda x: x.get(selected_grade, 0), reverse=True)


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
    """
    Loads and processes course data from the JS file. Then insert it into the MongoDB database.


    Returns:
        Redirects admin to the admin page with a message saying if the data was successful or failed.
    """
    try:
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

        # format the JSON data for the database
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
    """
    Scrapes faculty data from an external source and updates the MongoDB database.
    Calls run_scraper from scrap.py file
    """
    try:
        # Run the scraper to get faculty data then insert to db
        faculty_data = run_scraper()
        # print("Scraped Data:", faculty_data)  

        data_processor.insert_faculty_data(faculty_data)

    except Exception as e:
        flash(f"An error occurred during faculty scraping: {e}", "danger")

    return redirect(url_for("admin_page"))



@app.route("/clear_database", methods=["POST"])
def clear_database():
    """
    Clears MongoDB of all records from the grades and faculty collections
    Calls clear_all_collections from data_loader.py 
    """
    data_processor.clear_all_collections()
    return redirect(url_for("admin_page"))


# Helper function to build MongoDB queries
def build_course_query(department, course_class, instructor):
    """
    Creates a MongoDB query for fetching course and instructor data.
    The query is built based on the department, course class, and instructor parameters. 
    It maps the department's full name to its corresponding code and forms the appropriate
    query structure.

    Args:
        department (str): Full name of the department (e.g., 'Mathematics')
        course_class (str): Specific course class to search for (e.g., '111')
        instructor (str): Instructor name

    Returns:
        dict: MongoDB query dictionary to fetch relevant course and instructor data.
    """
    query = {}
    
    # Map the full actual department name back to its code for query
    # Otherwise the results won't show on user page
    department_code = None
    for code, full_name in NATURAL_SCIENCES_DEPARTMENTS.items():
        if full_name == department:
            department_code = code
            break

    # course "MATH111" match with actual name
    if department_code and course_class:
        query["course"] = f'{department_code}{course_class}'
    elif department_code:
        query["course"] = {'$regex': f'^{department_code}'}
    elif course_class:
        query["course"] = {'$regex': f'{course_class}$'}
    elif instructor:
        query["instructor"] = instructor
    
    return query




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)