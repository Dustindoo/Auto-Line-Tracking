from flask import Flask, render_template_string, request, redirect, url_for, send_file
import qrcode
import io
import datetime

app = Flask(__name__)

# In-memory data store for tasks
tasks = {
    1: {"name": "Task 1: Clean the kitchen", "completed": False, "completion_time": None},
    2: {"name": "Task 2: Take out the trash", "completed": False, "completion_time": None},
    3: {"name": "Task 3: Water the plants", "completed": False, "completion_time": None},
}
# Simple counter for new task IDs
next_task_id = 4

# --- HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Task List</title>
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
    <h1>Task Manager</h1>

    <!-- Form to Add New Task -->
    <form action="/add" method="post">
        <input type="text" name="task_name" placeholder="Enter a new task" required>
        <button type="submit">Add Task</button>
    </form>

    <!-- Task Table -->
    <table>
        <tr>
            <th>Task</th>
            <th>Status / Completion Time</th>
            <th>QR Code</th>
            <th>Actions</th>
        </tr>
        {% for task_id, task in tasks.items()|sort %}
        <tr>
            <td class="{{ 'completed-task' if task.completed else '' }}">{{ task.name }}</td>
            <td>
                {% if task.completed %}
                    Completed at: {{ task.completion_time.strftime('%Y-%m-%d %H:%M:%S') }}
                {% else %}
                    Pending
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
    task_name = request.form.get('task_name')
    if task_name:
        tasks[next_task_id] = {"name": task_name, "completed": False, "completion_time": None}
        next_task_id += 1
    return redirect(url_for('index'))

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if task_id not in tasks:
        return "Task not found", 404

    if request.method == 'POST':
        new_name = request.form.get('task_name')
        if new_name:
            tasks[task_id]['name'] = new_name
        return redirect(url_for('index'))

    edit_html = f"""
    <!DOCTYPE html><html><head><title>Edit Task</title></head><body>
    <h1>Edit Task</h1><form method="post">
    <input type="text" name="task_name" value="{tasks[task_id]['name']}" required>
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

# The following block is removed for production deployment
# as Gunicorn will be used to run the app.
# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5003)