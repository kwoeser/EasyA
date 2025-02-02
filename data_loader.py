import re
from pymongo import UpdateOne 
from flask import flash

class DataLoader:
    def __init__(self, db, NATURAL_SCIENCES_DEPARTMENTS):
        # Initialize with a mapping of department codes to full names
        self.db = db
        self.NATURAL_SCIENCES_DEPARTMENTS = NATURAL_SCIENCES_DEPARTMENTS

    # Format the instructor names in a last name first name order 
    # may have issues
    def clean_instructor_names(self, instructor_list):
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
        departments, classes = set(), set()
        for course in course_list:
            # Matches the department name and class number
            dept_match = re.findall(r'^[A-Za-z]+', course)
            num_match = re.findall(r'\d+', course)

            if dept_match and dept_match[0] in self.NATURAL_SCIENCES_DEPARTMENTS:
                departments.add(self.NATURAL_SCIENCES_DEPARTMENTS[dept_match[0]])
                if num_match:
                    classes.add(int(num_match[0]))

        return sorted(departments), sorted(classes)


    # Transforms the JSON course data that will be inputed from the admin page to be compatiable for the database 
    def transform_course_data(self, groups):
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
    
    def extract_department(class_code):
        # Extract the department name from the class code, stop when you run into the first character.
        # return all the characters before the first number
        for i, char in enumerate(class_code):
            if char.isdigit():
                return class_code[:i]  
            
        # print(extract_department("MATH111")) 
        return class_code  

    def extract_class_num(class_code):
        # Extract the class number from the class code
        # return everything after then characters end and only the numbers
        for i, char in enumerate(class_code):
            if char.isdigit():
                return class_code[i:]  

        return 
    

    # DATABASE SECTION
    # INSERTING SCRAPING DATA TO DATABASE 
    
    # ISSUES WITH INSERTING SCRAPED
    def insert_faculty_data(self, faculty_data):
        bulk_operations = []

        for entry in faculty_data:
            # Safely fetch the 'course_number' if it exists, otherwise None
            course_num = entry.get("course_number", None)
            name = entry["name"]
            department = entry["department"]

            bulk_operations.append(
                UpdateOne(
                    {
                        "name": name,
                        "department": department,
                        # Matches if 'course_number' is present, otherwise None
                        "course_number": course_num
                    },
                    {
                        "$set": {
                            "name": name,
                            "department": department,
                            "course_number": course_num
                        }
                    },
                    upsert=True
                )
            )

        if bulk_operations:
            self.db.faculty.bulk_write(bulk_operations, ordered=False)
            flash(f"Successfully merged {len(bulk_operations)} faculty records.", "success")
        else:
            flash("No faculty data found.", "warning")


    def merge_faculty_with_grades(self):
        # Merges faculty data into the grades collection by matching on instructor name.
        # Copies department (and course_number if present) from faculty into the grades record.
        
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
        try:
            grades_count = self.db.grades.count_documents({})
            faculty_count = self.db.faculty.count_documents({})
            self.db.grades.delete_many({})
            self.db.faculty.delete_many({})

            flash(f"Cleared {grades_count} grade records and {faculty_count} faculty records.", "success")
        except Exception as e:
            flash(f"An error occurred while clearing the database: {e}", "danger")





# class DatabaseManager:
#     def __init__(self, db):
#             self.db = db