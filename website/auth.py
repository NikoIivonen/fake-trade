from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from . import SYMBOLS

auth = Blueprint('auth', __name__)

def starter_balance():
    string = ''
    for symbol in SYMBOLS:
        value = '0'
        if symbol == 'CASH':
            value = '100000'
        string += value + symbol

    return string

def starter_loans():
    string = ''
    for symbol in SYMBOLS:
        if symbol != 'CASH':
            value = '0'
            string += value + symbol

    return string

def starter_expires():
    string = ''
    for symbol in SYMBOLS:
        if symbol != 'CASH':
            value = '0'
            string += value + symbol

    return string

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')


    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        error = False
        if user:
            flash('Email already exists.', category='error')
            error = True
        else:
            user = User.query.filter_by(first_name=first_name).first()
            if user:
                flash('Username is already taken.', category='error')
                error = True

        if not error:
            if len(email) < 4:
                flash('Email is not valid.', category='error')
            elif len(first_name) < 2:
                flash('Username must be at least 2 characters.', category='error')
            elif password1 != password2:
                flash('Passwords don\'t match.', category='error')
            elif len(password1) < 6:
                flash('Password must be at least 6 characters', category='error')
            else:
                new_user = User(email=email, first_name=first_name, password=generate_password_hash(password1, method='scrypt'), balance=starter_balance(), loan_amounts=starter_loans(), expire_dates=starter_expires(), closed=False, interests=starter_loans())
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user, remember=True)
                flash('Account created successfully!', category='success')
                return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)