from flask import Blueprint, render_template

auth = Blueprint('auth',__name__)

@auth.route('/auth')
def login():
    return render_template("login.html")

@auth.route('/logout')
def logout():
    return "Logout"

@auth.route('/signup')
def signup():
    return render_template("signup.html")