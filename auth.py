from flask import Blueprint, render_template, redirect, url_for
from flask import request
from models import db, User
from flask_login import login_user, logout_user, login_required
from views import log_visit

# Create a blueprint
auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/register', methods=['GET', 'POST'])
@auth_blueprint.route('/signup', methods=['GET', 'POST'])
def signup():
    log_visit(page="signup", user_id=None)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return redirect(url_for('auth.login'))

        # Create a new user
        new_user = User(email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('auth.login'))

    return render_template('signup.html')


@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    log_visit(page="login", user_id=None)

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()

        if not user:
            log_visit(page="login_error", user_id=None)
            return redirect(url_for('auth.login'))

        if not user.check_password(password):
            log_visit(page="login_error", user_id=user.id)
            return redirect(url_for('auth.login'))

        # Successful login
        login_user(user)
        return redirect(url_for('main.todo'))
        
    return render_template('login.html')

@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))