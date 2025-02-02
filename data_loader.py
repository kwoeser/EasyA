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
            try:
                cleaned_name = instructor.strip()
                match = re.match(r"^(\S+),\s*(\S+)(?:\s+(\S+))?", cleaned_name)

                if match:
                    last_name, first_name, middle_name = match.groups()
                    formatted_name = f"{last_name}, {first_name} {middle_name or ''}".strip()
                    clean_names.add(formatted_name)
                else:
                    clean_names.add(cleaned_name)
            except Exception as e:
                print(f"Error processing instructor '{instructor}': {e}")

        return clean_names

    # Extract the department name and class number from the class code
    # Uses regex instead of our previous method
    def extract_departments_and_classes(self, course_list):
        departments, classes = set(), set()
        for course in course_list:
            # Match department prefix (letters) and class number (digits)
            dept_match = re.match(r'^([A-Z]+)', course)
            num_match = re.search(r'(\d+)', course)

            if dept_match:
                dept_code = dept_match.group(1)
                # Filter only Natural Sciences based on known department codes
                if dept_code in self.NATURAL_SCIENCES_DEPARTMENTS:
                    departments.add(self.NATURAL_SCIENCES_DEPARTMENTS[dept_code])
                    if num_match:
                        classes.add(num_match.group(1))

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

    def extract_department(self, class_code):
        # Extract the department name from the class code, stop when you run into the first character.
        # return all the characters before the first number
        for i, char in enumerate(class_code):
            if char.isdigit():
                return class_code[:i]  

        return class_code  

    def extract_class_num(self, class_code):
        # Extract the class number from the class code
        # return everything after the characters end and only the numbers
        for i, char in enumerate(class_code):
            if char.isdigit():
                return class_code[i:]  

        return None

    # DATABASE SECTION
    # INSERTING SCRAPING DATA TO DATABASE 
    # ISSUES WITH INSERTING SCRAPED
    def insert_faculty_data(self, faculty_data):
        BATCH_SIZE = 1000  # Insert in batches of 1000
        bulk_operations = []
        missing_fields_count = 0
        total_inserted = 0

        for i, entry in enumerate(faculty_data):
            if all(key in entry for key in ["name", "department", "course_number"]):
                bulk_operations.append(
                    UpdateOne(
                        {"name": entry["name"], "department": entry["department"], "course_number": entry["course_number"]},
                        {"$set": entry},
                        upsert=True
                    )
                )
            else:
                missing_fields_count += 1

            if len(bulk_operations) >= BATCH_SIZE:
                result = self.db.faculty.bulk_write(bulk_operations, ordered=False)
                total_inserted += result.upserted_count or 0
                bulk_operations = []  # Clear batch after insert

        if bulk_operations:
            result = self.db.faculty.bulk_write(bulk_operations, ordered=False)
            total_inserted += result.upserted_count or 0

        flash(f"Successfully merged {total_inserted} faculty records.", "success")

        if missing_fields_count:
            print(f"Skipped {missing_fields_count} entries due to missing required fields.")

    def merge_faculty_with_grades(self):
        """
        Merge faculty data with grades collection based on department and instructor name.
        """
        faculty_records = list(self.db.faculty.find())
        bulk_operations = []

        for faculty in faculty_records:
            name = faculty.get("name")
            department = faculty.get("department")
            course_number = faculty.get("course_number")

            if name and department and course_number:
                course_code_pattern = f"{department}{course_number}"  # e.g., CIS210

                # Update grade records matching the department, course number, and instructor name
                bulk_operations.append(
                    UpdateOne(
                        {
                            "course": {"$regex": f"^{course_code_pattern}"},
                            "instructor": {"$regex": f"^{name}"}
                        },
                        {"$set": {"department": department, "instructor": name}},
                        upsert=False
                    )
                )

        if bulk_operations:
            result = self.db.grades.bulk_write(bulk_operations, ordered=False)
            print(f"Successfully merged {result.modified_count} grade records with faculty data.")
        else:
            print("No matching records found for merging.")



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
