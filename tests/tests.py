import unittest
from unittest.mock import patch
from pymongo import MongoClient
import mongomock  # Fake MongoDB for testing

from data_loader import DataLoader

# Mock database connection
mock_db = mongomock.MongoClient().db

# Sample test data
SAMPLE_FACULTY_DATA = [
    {"name": "Doe, John", "department": "CIS", "course_number": "101"},
    {"name": "Smith, Alice", "department": "MATH", "course_number": "201"},
]

SAMPLE_GRADE_DATA = [
    {"course": "CIS101", "term": "Fall 2023", "aprec": 50.0, "bprec": 30.0, "cprec": 10.0, "dprec": 5.0, "fprec": 5.0, "instructor": "Doe, John"},
    {"course": "MATH201", "term": "Spring 2023", "aprec": 40.0, "bprec": 30.0, "cprec": 20.0, "dprec": 5.0, "fprec": 5.0, "instructor": "Smith, Alice"},
]

class TestDatabaseOperations(unittest.TestCase):

    def setUp(self):
        """Set up a mock MongoDB instance before each test."""
        self.mock_db = mongomock.MongoClient().db
        self.data_loader = DataLoader(self.mock_db, {})

    def tearDown(self):
        """Clean up after each test."""
        self.mock_db.faculty.delete_many({})
        self.mock_db.grades.delete_many({})

    def test_insert_faculty_data(self):
        """Test if faculty data is inserted correctly into MongoDB."""
        self.data_loader.insert_faculty_data(SAMPLE_FACULTY_DATA)

        stored_faculty = list(self.mock_db.faculty.find({}))
        self.assertEqual(len(stored_faculty), 2)  

        # Validate stored data
        self.assertEqual(stored_faculty[0]["name"], "Doe, John")
        self.assertEqual(stored_faculty[0]["department"], "CIS")
        self.assertEqual(stored_faculty[1]["name"], "Smith, Alice")
        self.assertEqual(stored_faculty[1]["department"], "MATH")

    def test_insert_grade_data(self):
        """Test if grade data is inserted correctly into MongoDB."""
        self.mock_db.grades.insert_many(SAMPLE_GRADE_DATA)

        stored_grades = list(self.mock_db.grades.find({}))
        self.assertEqual(len(stored_grades), 2)  

        # Validate stored data
        self.assertEqual(stored_grades[0]["course"], "CIS101")
        self.assertEqual(stored_grades[0]["aprec"], 50.0)
        self.assertEqual(stored_grades[1]["course"], "MATH201")
        self.assertEqual(stored_grades[1]["aprec"], 40.0)

    def test_merge_faculty_with_grades(self):
        """Test merging faculty data into grades collection."""
        self.mock_db.faculty.insert_many(SAMPLE_FACULTY_DATA)
        self.mock_db.grades.insert_many(SAMPLE_GRADE_DATA)

        self.data_loader.merge_faculty_with_grades()

        updated_grades = list(self.mock_db.grades.find({}))
        self.assertEqual(updated_grades[0]["department"], "CIS")
        self.assertEqual(updated_grades[1]["department"], "MATH")

    def test_clear_database(self):
        """Test if the database clears correctly."""
        self.mock_db.faculty.insert_many(SAMPLE_FACULTY_DATA)
        self.mock_db.grades.insert_many(SAMPLE_GRADE_DATA)

        self.data_loader.clear_all_collections()

        self.assertEqual(self.mock_db.faculty.count_documents({}), 0)
        self.assertEqual(self.mock_db.grades.count_documents({}), 0)

if __name__ == "__main__":
    unittest.main()
