import pandas as pd
import os
from flask import Flask, render_template_string, request, redirect, url_for, send_file

import qrcode
import io
import datetime

app = Flask(__name__)

# Create an 'uploads' directory if it doesn't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# In-memory data store for tasks
tasks = {
    1: {"project": "Home", "sub_line": "Kitchen", "name": "Clean the kitchen", "completed": False, "completion_time": None},
    2: {"project": "Home", "sub_line": "General", "name": "Take out the trash", "completed": False, "completion_time": None},
    3: {"project": "Garden", "sub_line": "Plants", "name": "Water the plants", "completed": False, "completion_time": None},
}
# Simple counter for new task IDs
next_task_id = 4

# --- HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Local Task List</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: auto; padding: 20px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .completed-task { text-decoration: line-through; color: grey; }
        form { margin-bottom: 20px; }
        input[type="text"] { width: 70%; padding: 8px; }
        button { padding: 9px 15px; }
        .actions a { margin-right: 10px; }
    </style>
</head>
<body>
    <h1>Local Task Manager</h1>

    <!-- Form to Add New Task -->
    <form action="/add" method="post">
        <input type="text" name="project" placeholder="Project" required>
        <input type="text" name="sub_line" placeholder="Sub Line" required>
        <input type="text" name="task_name" placeholder="Enter a new task" required>
        <button type="submit">Add Task</button>
    </form>

    <!-- Form to Upload Excel File -->
    <form action="/upload" method="post" enctype="multipart/form-data" style="display: inline-block;">
        <input type="file" name="excel_file" accept=".xlsx, .xls" required>
        <button type="submit">Upload Excel</button>
    </form>

    <!-- Download Excel Link -->
    <a href="/download" style="display: inline-block; margin-left: 10px;"><button>Download Excel</button></a>

    <!-- Task Table -->
    <table>
        <tr>
            <th>Project</th>
            <th>Sub Line</th>
            <th>Task</th>
            <th>Status</th>
            <th>Completion Time</th>
            <th>QR Code</th>
            <th>Actions</th>
        </tr>
        {% for task_id, task in tasks.items()|sort %}
        <tr>
            <td class="{{ 'completed-task' if task.completed else '' }}">{{ task.project }}</td>
            <td class="{{ 'completed-task' if task.completed else '' }}">{{ task.sub_line }}</td>
            <td class="{{ 'completed-task' if task.completed else '' }}">{{ task.name }}</td>
            <td>
                {% if task.completed %}
                    Completed
                {% else %}
                    Pending
                {% endif %}
            </td>
            <td>
                {% if task.completion_time %}
                    {{ task.completion_time.strftime('%Y-%m-%d %H:%M:%S') }}
                {% else %}
                    -
                {% endif %}
            </td>
            <td><img src="/qr/{{ task_id }}" alt="QR Code for task {{ task_id }}" width="100" height="100"></td>
            <td class="actions">
                <a href="/edit/{{ task_id }}">Edit</a>
                <a href="/delete/{{ task_id }}" onclick="return confirm('Are you sure?');">Delete</a>
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# --- Routes ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    global next_task_id
    project = request.form.get('project')
    sub_line = request.form.get('sub_line')
    task_name = request.form.get('task_name')
    if task_name and project and sub_line:
        tasks[next_task_id] = {
            "project": project,
            "sub_line": sub_line,
            "name": task_name,
            "completed": False,
            "completion_time": None
        }
        next_task_id += 1
    return redirect(url_for('index'))

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if task_id not in tasks:
        return "Task not found", 404

    if request.method == 'POST':
        tasks[task_id]['project'] = request.form.get('project', tasks[task_id]['project'])
        tasks[task_id]['sub_line'] = request.form.get('sub_line', tasks[task_id]['sub_line'])
        tasks[task_id]['name'] = request.form.get('task_name', tasks[task_id]['name'])
        return redirect(url_for('index'))

    task = tasks[task_id]
    edit_html = f"""
    <!DOCTYPE html><html><head><title>Edit Task</title></head><body>
    <h1>Edit Task</h1><form method="post">
    <input type="text" name="project" value="{task['project']}" required><br>
    <input type="text" name="sub_line" value="{task['sub_line']}" required><br>
    <input type="text" name="task_name" value="{task['name']}" required><br>
    <button type="submit">Update</button></form><a href="/">Cancel</a>
    </body></html>
    """
    return render_template_string(edit_html)

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    if task_id in tasks:
        del tasks[task_id]
    return redirect(url_for('index'))

@app.route('/qr/<int:task_id>')
def generate_qr(task_id):
    if task_id not in tasks:
        return "Task not found", 404
    
    confirm_url = request.host_url + f"confirm/{task_id}"
    
    img = qrcode.make(confirm_url)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png')

@app.route('/confirm/<int:task_id>')
def confirm_task(task_id):
    if task_id not in tasks:
        return "Task not found", 404
        
    if not tasks[task_id]["completed"]:
        tasks[task_id]["completed"] = True
        tasks[task_id]["completion_time"] = datetime.datetime.now()
    
    return f"<h1>Task '{tasks[task_id]['name']}' confirmed!</h1><p><a href='/'>Back to list</a></p>"

@app.route('/upload', methods=['POST'])
def upload_excel():
    global next_task_id
    if 'excel_file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['excel_file']
    if file.filename == '':
        return redirect(url_for('index'))

    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        # Ensure the 'uploads' directory exists
        if not os.path.exists('uploads'):
            os.makedirs('uploads')
        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)

        try:
            df = pd.read_excel(filepath)
            for index, row in df.iterrows():
                project = row['Project']
                sub_line = row['Sub Line']
                task_name = row['Task']
                tasks[next_task_id] = {
                    "project": project,
                    "sub_line": sub_line,
                    "name": task_name,
                    "completed": False,
                    "completion_time": None
                }
                next_task_id += 1
        except Exception as e:
            return f"Error processing Excel file: {e}"

    return redirect(url_for('index'))

@app.route('/download')
def download_excel():
    # Convert tasks dictionary to a list of dictionaries
    task_list = []
    for task_id, task_details in tasks.items():
        task_list.append({
            'Project': task_details.get('project', ''),
            'Sub Line': task_details.get('sub_line', ''),
            'Task': task_details.get('name', ''),
            'Status': 'Completed' if task_details.get('completed') else 'Pending',
            'Completion Time': task_details.get('completion_time', None)
        })

    # Create a DataFrame
    df = pd.DataFrame(task_list)

    # Format the completion time column
    if 'Completion Time' in df.columns:
        df['Completion Time'] = pd.to_datetime(df['Completion Time']).dt.strftime('%Y-%m-%d %H:%M:%S')

    # Create an in-memory Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Tasks')
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='tasks.xlsx'
    )