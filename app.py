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



# might delete (we need to find another way to extract departments unless we decide another way)
def extract_department(class_code):
    if len(class_code) > 3 and class_code[3].isdigit():
        return class_code[:3]
    return class_code[:2]


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

    # Populate dropdown data
    departments_set = set()
    classes_set = set()
    teachers_set = set()

    for classes, entries in data.items():
        # Department is the first 3 characters
        # Maybe issues beause all departments aren't 3 characters? AA is issue
        departments_set.add(classes[:3])  
        classes_set.add(classes)
        for entry in entries:
            teachers_set.add(entry['instructor'])

    # Get filters from the query string
    selected_department = request.args.get('department', '')
    selected_class = request.args.get('class', '')
    selected_teacher = request.args.get('teacher', '')

    # Filter results
    # ISSUES WITH FILTERING RESULTS
    results = []
    for classes, entries in data.items():
        if selected_department and not classes.startswith(selected_department):
            continue
        if selected_class and classes != selected_class:
            continue

        for entry in entries:
            if selected_teacher and entry['instructor'] != selected_teacher:
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
        classes=sorted(classes),
        teachers=sorted(teachers_set),
        results=results
    )



if __name__ == '__main__':
    app.run(debug=True)
