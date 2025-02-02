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
            print(f"Extracting department and class from: {course}, Dept Match: {dept_match}, Class Match: {num_match}")

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
        # Inserting multiple UpdateOne operations into the database from one bulk operations list
        bulk_operations = []
        bulk_grade_ops = []

        for entry in faculty_data:
            # print("Inserting entry:", entry)
            print("INSERTING COURSE:", entry.get("course"))
            bulk_operations.append(
                UpdateOne(
                    {"name": entry["name"], "department": entry["department"], "course_number": entry["course_number"]},
                    {"$set": entry},
                    upsert=True
                )
            )

            # update the grades collection if course information is tied to faculty.
            # Construct course name properly and insert into grades collection
            # Fixes the scraper dropdown data not appearing on user page
            course = entry["department"] + entry["course_number"]
            if course.strip():
                bulk_grade_ops.append(
                    UpdateOne(
                        {"course": course, "instructor": entry["name"]},
                        {
                            "$setOnInsert": {
                                "term": entry.get("term", ""),
                                "instructor": entry["name"]
                            }
                        },
                        upsert=True
                    )
                )

        # Faculty records
        if bulk_operations:
            self.db.faculty.bulk_write(bulk_operations, ordered=False)
            flash(f"Successfully merged {len(bulk_operations)} faculty records.", "success")
        else:
            flash("No faculty data found.", "warning")

     
        if bulk_grade_ops:
            self.db.grades.bulk_write(bulk_grade_ops, ordered=False)



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