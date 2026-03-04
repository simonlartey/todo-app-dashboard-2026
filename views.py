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


@main_blueprint.route('/dashboard', methods=['GET'])
def dashboard():

    today = datetime.datetime.utcnow().date()
    week_ago = today - datetime.timedelta(days=6)

    # ===== Basic Metrics =====
    total_users = User.query.count()

    new_users = User.query.filter(
        User.created_at >= week_ago
    ).count()

    visits_today = Visit.query.filter(
        db.func.date(Visit.timestamp) == today
    ).count()

    waitlist_this_week = Waitlist.query.filter(
        Waitlist.timestamp >= week_ago
    ).all()

    recent_visits = Visit.query.order_by(
        Visit.timestamp.desc()
    ).limit(15).all()

    # ===== Weekly Index Visit Comparison =====

    week_visits = []
    two_week_visits = []
    chart_week = []

    for i in range(6, -1, -1):
        day_this_week = today - datetime.timedelta(days=i)
        day_last_week = day_this_week - datetime.timedelta(days=7)

        chart_week.append(day_this_week.strftime("%a"))

        this_week_count = Visit.query.filter(
            Visit.page == "index",
            db.func.date(Visit.timestamp) == day_this_week
        ).count()

        last_week_count = Visit.query.filter(
            Visit.page == "index",
            db.func.date(Visit.timestamp) == day_last_week
        ).count()

        week_visits.append(this_week_count)
        two_week_visits.append(last_week_count)

    # ===== Bar Chart: Visits Today Per Page =====

    pages = [
        "index",
        "login-g",
        "callback",
        "user-name",
        "license",
        "waitlist",
        "state-not-found",
        "State-mismatch"
    ]

    page_visits = []

    for page in pages:
        count = Visit.query.filter(
            Visit.page == page,
            db.func.date(Visit.timestamp) == today
        ).count()

        page_visits.append(count)

    this_week_total = sum(week_visits)
    last_week_total = sum(two_week_visits)

    if last_week_total > 0:
        productivity_change = round(
            ((this_week_total - last_week_total) / last_week_total) * 100,
            1
        )
    else:
        productivity_change = 0

    return render_template(
        'admin.html',
        date=datetime.datetime.now().strftime("%B %d, %Y"),
        total_users=total_users,
        new_users=new_users,
        visits_today=visits_today,
        productivity_change=productivity_change,
        visits=recent_visits,
        waitlist=waitlist_this_week,
        chart_week=chart_week,
        page_visits=page_visits,
        week_visits=week_visits,
        two_week_visits=two_week_visits,
        users=User.query.all(),
        tasks=Task.query.all()
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