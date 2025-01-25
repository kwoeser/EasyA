from flask import Flask, request, send_file, render_template
import json

app = Flask(__name__)

# Handle loading grade data
DATA_FILE = "gradedata.json"
def load_grade_data():
    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)  
        return data
    
    except FileNotFoundError:
        return {"error": f"File {DATA_FILE} not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format in the file"}


def extract_department(class_code):
    # extract the department name from the class code, stop when you run into the first character.
    # return all the characters before the first number

    for i, char in enumerate(class_code):
        if char.isdigit():
            return class_code[:i]  
        
    # print(extract_department("MATH111")) 
    return class_code  

def extract_class_num(class_code):
    # extract the class number from the class code
    # return everything after then characters end and only the numbers

    for i, char in enumerate(class_code):
        if char.isdigit():
            return class_code[i:]  

    return 



@app.route('/admin', methods=['GET'])
def admin_page():
    return render_template('admin_page.html')

# Adding data
# @app.route('/admin', methods=['POST'])
# def admin_page():
#     return render_template('admin_page.html')

# Deleting data
# @app.route('/admin', methods=['DELETE'])
# def admin_page():
#     return render_template('admin_page.html')


# WAS RUNNING BUT ERROR
# User page and index page 
@app.route('/', methods=['GET'])
def user_page():
    data = load_grade_data()

    # Store and populate dropdown data
    departments_set = set()
    classes_set = set()
    teachers_set = set()

    for classes, entries in data.items():
        # Department is the first 3 characters
        # Maybe issues beause all departments aren't 3 characters? AA is issue
        # print(extract_department("MATH111")) 
        departments_set.add(extract_department(classes))  
        classes_set.add(extract_class_num(classes))

        for entry in entries:
            teachers_set.add(entry['instructor'])

        
    selected_department = request.args.get('department', '')
    selected_class = request.args.get('class', '')
    selected_teacher = request.args.get('teacher', '')

    # Filter ultsres
    # ISSUES WITH FILTERING RESULTS, make changes to handle 
    results = []
    for classes, entries in data.items():
        department = extract_department(classes)
        class_num = extract_class_num(classes)
        if selected_department and not department:
            continue
        if selected_class and not class_num:
            continue

        for entry in entries:
            if selected_teacher and not entry['instructor']:
                continue

            # append results but only append a percentage. WILL PROBABLY CHANGE TO STORE ALL GRADES
            results.append({
                'class': classes,
                'teacher': entry['instructor'],
                'percent_a': entry['aprec'],
                'term': entry['TERM_DESC']
            })

    return render_template(
        'user_page.html',
        departments=sorted(departments_set),
        classes=sorted(classes_set),
        teachers=sorted(teachers_set),
        results=results
    )



if __name__ == '__main__':
    app.run(debug=True)
