import random
from flask import Blueprint, render_template, redirect, url_for
from flask import request
from flask_login import login_required, current_user
from models import db, Task, User, Visit, Waitlist
from sqlalchemy.exc import IntegrityError
# import datetime
import datetime

# Create a blueprint
main_blueprint = Blueprint('main', __name__)


def log_visit(page, user_id):
    """Log a visit to a page by a user."""
    visit = Visit(page=page, user=user_id)
    db.session.add(visit)
    db.session.commit()


###############################################################################
# Routes
###############################################################################


@main_blueprint.route('/', methods=['GET'])
def index():
    log_visit(page='index', user_id=current_user.id if current_user.is_authenticated else None)

    # print all visits
    visits = Visit.query.all()
    for visit in visits:
        print(f"Visit: {visit.page}, User ID: {visit.user}, Timestamp: {visit.timestamp}")

    return render_template('index.html')

@main_blueprint.route('/invitation', methods=['GET', 'POST'])
def invitation():

    log_visit(
        page='invitation',
        user_id=current_user.id if current_user.is_authenticated else None
    )

    if request.method == 'POST':
        email = request.form['email']

        try:
            existing_signup = Waitlist.query.filter_by(email=email).first()

            if not existing_signup:
                new_signup = Waitlist(email=email)
                db.session.add(new_signup)
                db.session.commit()

                log_visit(
                    page='waitlist_signup',
                    user_id=current_user.id if current_user.is_authenticated else None
                )

        except IntegrityError:
            db.session.rollback()

    return render_template('invitation.html')


@main_blueprint.route('/todo', methods=['GET', 'POST'])
@login_required
def todo():

    log_visit(page='todo', user_id=current_user.id)

    return render_template('todo.html')


@main_blueprint.route('/dashboard', methods=['GET', 'POST'])
# @login_required
def dashboard():
    visits = Visit.query.all()

    chart_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    week_notes = [random.randint(0, 15) for _ in range(7)]
    two_week_notes = [random.randint(0, 15) for _ in range(7)]

    return render_template('admin.html',
                           date=datetime.datetime.now().strftime("%B %d, %Y"),
                           total_users=716,     # add real number
                           new_users=5,         # add real number
                           visits_today=120,    # add real number
                           productivity_change=0.6,   # add real number
                           visits=visits,           # add real value
                           chart_week=chart_week,   # update list to show today as the last day in the chart
                           week_notes=week_notes,   # add real values
                           two_week_notes=two_week_notes  # add real values
                           )



@main_blueprint.route('/api/v1/tasks', methods=['GET'])
@login_required
def api_get_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return {
        "tasks": [task.to_dict() for task in tasks]
    }


@main_blueprint.route('/api/v1/tasks', methods=['POST'])
@login_required
def api_create_task():
    data = request.get_json()
    new_task = Task(title=data['title'], user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()
    log_visit(page='create_task', user_id=current_user.id)
    return {
        "task": new_task.to_dict()
    }, 201


@main_blueprint.route('/api/v1/tasks/<int:task_id>', methods=['PATCH'])
@login_required
def api_toggle_task(task_id):
    task = Task.query.get(task_id)

    if task is None:
        return {"error": "Task not found"}, 404

    task.toggle()
    db.session.commit()
    log_visit(page='toggle_task', user_id=current_user.id)

    return {"task": task.to_dict()}, 200


@main_blueprint.route('/remove/<int:task_id>')
@login_required
def remove(task_id):
    task = Task.query.get(task_id)

    if task is None:
        return redirect(url_for('main.todo'))

    db.session.delete(task)
    db.session.commit()
    log_visit(page='delete_task', user_id=current_user.id)

    return redirect(url_for('main.todo'))