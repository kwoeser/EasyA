import re
from pymongo import UpdateOne 
from flask import flash

class DataLoader:
    """
    A class to handle data processing, transformation, and database interactions
    for faculty and grade records in a MongoDB database.

    ...

    Attributes
    ----------
    db : pymongo.database.Database
        The MongoDB database connection.
    NATURAL_SCIENCES_DEPARTMENTS : dict
        A mapping of department codes to full department names.


    Methods
    -------
    clean_instructor_names(instructor_list):
        Format the instructor names in a last name first name order

    extract_departments_and_classes(course_list):
        Extracts departments and course numbers from a the course codes list.

    normalize_name(name):
        Normalizes instructor names by capitalizing the first letter of the last and first names.

    transform_course_data(groups):
        Transforms the JSON course data that will be inputed from the admin page to be compatiable for 
        MongoDB insertion.

    insert_faculty_data(faculty_data):
        Inserts scraped faculty data into the MongoDB faculty collection.
        Normalizes faculty names before insertion. 
        
    merge_faculty_with_grades():
        Merges faculty data into the grades collection by associating instructors
        with their respective departments and course numbers.

    clear_all_collections():
        Clears all records from the grades and faculty collections in MongoDB.
    """


    def __init__(self, db, NATURAL_SCIENCES_DEPARTMENTS):
        """
        Initializes the DataLoader with the database and a mapping of department codes to their full names.
        NATURAL_SCIENCES_DEPARTMENTS will be grabbed from app.py

        Parameters:
            db (pymongo.database.Database): The MongoDB database connection.
            NATURAL_SCIENCES_DEPARTMENTS (dict): Mapping of department codes to full department names.
        """
        self.db = db
        self.NATURAL_SCIENCES_DEPARTMENTS = NATURAL_SCIENCES_DEPARTMENTS

    
    def clean_instructor_names(self, instructor_list):
        """
        Format the instructor names in a last name first name order 

        Parameters:
            instructor_list (list): List of instructor names to be cleaned.

        Returns:
            set: A set of cleaned instructor names.
        """
        clean_names = set()
        for instructor in instructor_list:
            cleaned_name = instructor.strip()
            match = re.match(r"^(\S+),\s*(\S+)(?:\s+(\S+))?", cleaned_name)

            if match:
                last_name, first_name, middle_name = match.groups()
                formatted_name = f"{last_name}, {first_name} {middle_name or ''}".strip()
                clean_names.add(formatted_name)
            else:
                clean_names.add(cleaned_name)

        return clean_names


    # Extract the department name and class number from the class code
    # Uses regex instead of our previous method
    def extract_departments_and_classes(self, course_list):
        """
        Extracts departments and course numbers from a the course codes list.

        Parameters:
            course_list (list): List of course codes (e.g., 'CIS210').

        Returns:
            tuple: A tuple containing sorted lists of departments and course numbers.
        """
        departments, classes = set(), set()
        for course in course_list:
            # Matches the department name and class number
            dept_match = re.findall(r'^[A-Za-z]+', course)
            num_match = re.findall(r'\d+', course)

            # print(f"Extracting department and class from: {course}, Dept Match: {dept_match}, Class Match: {num_match}")
            if dept_match and dept_match[0] in self.NATURAL_SCIENCES_DEPARTMENTS:
                departments.add(self.NATURAL_SCIENCES_DEPARTMENTS[dept_match[0]])
                if num_match:
                    classes.add(int(num_match[0]))

        return sorted(departments), sorted(classes)


    def normalize_name(self, name):
        """
        Normalizes instructor names by capitalizing the first letter of the last and first names.

        Parameters:
            name (str): Instructor name in any format.

        Returns:
            str: Normalized name in the format "Last Name, First Name".
        """
        if not name:
            return ""
        parts = name.strip().lower().split(',')
        last_name = parts[0].strip().capitalize()
        first_name = parts[1].strip().split()[0].capitalize() if len(parts) > 1 else ''
        return f"{last_name}, {first_name}"


    def transform_course_data(self, groups):
        """
        Transforms the JSON course data that will be inputed from the admin page to be compatiable for 
        MongoDB insertion.

        Parameters:
            groups (dict): JSON-like dictionary containing historical course data.

        Returns:
            list: A list of formatted course records for database insertion.
        """
        records = []

        for course, details in groups.items():
            for entry in details:
                records.append({
                    "course": course,
                    "term": entry.get("TERM_DESC", ""),
                    "aprec": float(entry.get("aprec", 0.0)),
                    "bprec": float(entry.get("bprec", 0.0)),
                    "cprec": float(entry.get("cprec", 0.0)),
                    "crn": entry.get("crn", "N/A"),
                    "dprec": float(entry.get("dprec", 0.0)),
                    "fprec": float(entry.get("fprec", 0.0)),
                    "instructor": entry.get("instructor", "Unknown"),
                })
                
        return records 



    # DATABASE SECTION, possibly make into seperate class or file
    # INSERTING SCRAPING DATA TO DATABASE 
    def insert_faculty_data(self, faculty_data):
        """
        Inserts scraped faculty data into the MongoDB faculty collection.
        Normalizes faculty names before insertion. 
        Will be used in app.py after scrap.py is ran.

        Parameters:
            faculty_data (list): List of dictionaries containing faculty details.
        """
        bulk_operations = []

        for entry in faculty_data:

            course_num = entry.get("course_number", None)
            name = self.normalize_name(entry.get("name", "Unknown"))
            department = entry.get("department", "Unknown")
            # print("Inserting entry:", entry)
            # print("INSERTING COURSE:", entry.get("course"))

            bulk_operations.append(
                UpdateOne(
                    {"name": name, "department": department, "course_number": course_num},
                    {"$set": {"name": name, "department": department, "course_number": course_num}},
                    upsert=True
                )
            )

        if bulk_operations:
            self.db.faculty.bulk_write(bulk_operations, ordered=False)
            flash(f"Successfully merged {len(bulk_operations)} faculty records.", "success")
        else:
            flash("No faculty data found.", "warning")


    def transform_course_data(self, groups):
        """
        Transforms raw JSON course data into a structured format for MongoDB.

        Parameters:
            groups (dict): JSON-like dictionary containing course data.

        Returns:
            list: A list of formatted course records for database insertion.
        """
        records = []

        for course, details in groups.items():
            for entry in details:
                instructor = self.normalize_name(entry.get("instructor", "Unknown"))
                records.append({
                    "course": course,
                    "term": entry.get("TERM_DESC", ""),
                    "aprec": float(entry.get("aprec", 0.0)),
                    "bprec": float(entry.get("bprec", 0.0)),
                    "cprec": float(entry.get("cprec", 0.0)),
                    "crn": entry.get("crn", "N/A"),
                    "dprec": float(entry.get("dprec", 0.0)),
                    "fprec": float(entry.get("fprec", 0.0)),
                    "instructor": instructor,
                })

        return records


    def merge_faculty_with_grades(self):
        """
        Merges faculty data into the grades collection by associating instructors
        with their respective departments and course numbers.
        """
        try:
            faculty_records = list(self.db.faculty.find())
            updates = []

            for record in faculty_records:
                name = record["name"]  
                department = record.get("department", None)
                course_num = record.get("course_number", None)

                updates.append(
                    UpdateOne(
                        {"instructor": name},
                        {"$set": {"department": department, "course_number": course_num}},
                        upsert=False
                    )
                )

            if updates:
                result = self.db.grades.bulk_write(updates, ordered=False)
                flash(f"Merged {result.modified_count} grade records with faculty data.", "success")
            else:
                flash("No matching records found for merging.", "info")

        except Exception as e:
            flash(f"Error merging faculty with grades: {e}", "danger")



    # Clears the database
    def clear_all_collections(self):
        """
        Clears all records from the grades and faculty collections in MongoDB.
        """
        try:
            grades_count = self.db.grades.count_documents({})
            faculty_count = self.db.faculty.count_documents({})
            self.db.grades.delete_many({})
            self.db.faculty.delete_many({})

            flash(f"Cleared {grades_count} grade records and {faculty_count} faculty records.", "success")
        except Exception as e:
            flash(f"An error occurred while clearing the database: {e}", "danger")

