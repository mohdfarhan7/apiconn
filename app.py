import os
from datetime import datetime
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

####################################################
# CONFIGURE FLASK
####################################################
app = Flask(__name__)

# --------------------------------------------
# CONNECTION STRING FOR SQL SERVER
# --------------------------------------------
# Replace "DashboardDB" with your desired DB name.
# If your DB name is "YourDB", set database_name accordingly.
database_name = "DashboardDB"

# Server name from your request:
server_name = "DESKTOP-JB047C5\\SQLEXPRESS"

# ODBC Driver 17 for SQL Server, Trusted Connection
db_driver = "ODBC+Driver+17+for+SQL+Server"

# Trusted connection: no user/pwd, uses Windows auth
connection_string = (
    f"mssql+pyodbc://{server_name}/{database_name}"
    f"?driver={db_driver}&trusted_connection=yes"
)

app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

####################################################
# MODELS
####################################################

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Open')  # "Open", "In Progress", "Completed"
    assigned_to = db.Column(db.Integer, db.ForeignKey('employees.id'))

class Shift(db.Model):
    __tablename__ = 'shifts'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    start_time = db.Column(db.String(50), nullable=False)
    end_time = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Active')

    # Relationship
    employee = db.relationship("Employee", backref="shifts")

class TimeOffRequest(db.Model):
    __tablename__ = 'timeoff_requests'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    start_date = db.Column(db.String(50), nullable=False)
    end_date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # "Pending", "Approved", "Denied"

class Performance(db.Model):
    __tablename__ = 'performance'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), default='')  # e.g. "Mon", "Tue", etc.
    tasks_completed = db.Column(db.Integer, default=0)
    hours_worked = db.Column(db.Integer, default=0)

class ActivityLog(db.Model):
    __tablename__ = 'activity_log'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

####################################################
# ENDPOINTS
####################################################

@app.route('/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """
    Returns:
      {
        "activeEmployees": <int>,
        "openTasks": <int>,
        "todaysShifts": <int>,
        "timeOffRequests": <int>
      }
    """
    active_employees = Employee.query.filter_by(is_active=True).count()
    open_tasks = Task.query.filter_by(status='Open').count()
    todays_shifts = Shift.query.filter_by(status='Active').count()
    pending_requests = TimeOffRequest.query.filter_by(status='Pending').count()

    summary_data = {
        "activeEmployees": active_employees,
        "openTasks": open_tasks,
        "todaysShifts": todays_shifts,
        "timeOffRequests": pending_requests
    }
    return jsonify(summary_data), 200

@app.route('/activities', methods=['GET'])
def get_activities():
    """
    Returns up to 10 recent activity items, sorted by timestamp descending.
    """
    activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
    results = []
    for a in activities:
        results.append({
            "description": a.description,
            "timestamp": a.timestamp.isoformat()
        })
    return jsonify(results), 200

@app.route('/performance', methods=['GET'])
def get_performance():
    """
    Returns performance data for the line chart:
      [
        { "date": ..., "tasks_completed": ..., "hours_worked": ... },
        ...
      ]
    """
    perf_records = Performance.query.all()
    results = []
    for p in perf_records:
        results.append({
            "date": p.date,
            "tasks_completed": p.tasks_completed,
            "hours_worked": p.hours_worked
        })
    return jsonify(results), 200

@app.route('/shifts', methods=['GET'])
def get_shifts():
    """
    Returns a list of current shifts, joining to employee data:
    [
      {
        "employee": "Firstname Lastname",
        "department": "...",
        "shiftTime": "start - end",
        "status": "Active"
      },
      ...
    ]
    """
    from sqlalchemy.orm import joinedload
    # Eager load employee
    shifts = Shift.query.options(joinedload(Shift.employee)).all()

    results = []
    for s in shifts:
        results.append({
            "employee": f"{s.employee.first_name} {s.employee.last_name}",
            "department": s.employee.department,
            "shiftTime": f"{s.start_time} - {s.end_time}",
            "status": s.status
        })
    return jsonify(results), 200

####################################################
# TABLE CREATION & APP RUN
####################################################

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Tables created (if not already present).")

    # Typically we wouldn't run the dev server in Docker,
    # but let's keep it for local debugging:
    app.run(debug=True, port=5000)
