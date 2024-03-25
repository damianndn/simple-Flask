from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, data_sources
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user, logout_user
from sqlalchemy.inspection import inspect
from .meme import *
import time
import asyncio

auth = Blueprint('auth',__name__)

inspector = inspect(User)

headings = inspector.mapper.column_attrs.keys()


@auth.route('/auth',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password,password):
                flash('Logged in successfully!',category='success')
                login_user(user,remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Unsuccessfull, try again',category='error')
        else:
            flash('No account existed under this email! Try again or Sign up...',category='error')

    return render_template("login.html")

@auth.route('/logout')
@login_required #can only access log out option if logged in
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/signup',methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('User already existed', category='error')
        elif len(email) <4 :
            flash('Email must be at least 4 characters.',category='error')
        elif len(firstName) < 2:
            flash('First name must be at least 2 characters',category='error')
        elif password1!=password2:
            flash('Passwords do NOT match, try again!',category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.',category='error')
        else:
            new_user = User(email=email,first_name=firstName,password=generate_password_hash(password1,method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash('Account created!',category='success')
            return redirect(url_for('views.home'))

    return render_template("signup.html")

@auth.route('/admin',methods=['GET','POST'])
def admin():
    if request.method == 'POST' and request.form.get('email')!= '':
        search_key_email = '%'+request.form.get('email')+'%'
        users = User.query.filter(User.email.like(search_key_email)).all()
        return render_template("admin.html",headings=headings,users=users)
    return render_template("admin.html",headings=headings,users='')

@auth.route('/meme',methods=['POST'])
async def meme():
    if 'btn1' in request.form:
        line = 'jaja'
    elif 'btn2' in request.form:
        line = '55'
    elif 'btn3' in request.form:
        line = 'heehee'
    else:
        start_time = time.time()
        listFolder = ""
        out=[]
        username = "administrator"
        password = "77@NguyenQuyDuc"
        findFolders(listFolder,out) #now 'out' list has been filled
        print("Exec time lasted --- %s seconds ---" % (time.time() - start_time))

        display_id = [] 
        allFolders = out
        findDislays(allFolders,display_id)
        display_id.sort()
        print("Exec time lasted --- %s seconds ---" % (time.time() - start_time))

        urls = [f"https://192.168.10.202/pivision/utility/api/v1/displays/{graphic}/export" for graphic in display_id]
        
        jsons = await main(urls,username,password)

        inverse = {}
        for k, v in jsons.items():
            if v != []:
                for x in v:
                    if isinstance(x, list):
                        for item in x:
                            inverse.setdefault(item, []).append(k)
                    else:
                        inverse.setdefault(x, []).append(k)
        

        if data_sources.query.count() != 0:
            # Clear existing data from the table
            db.session.query(data_sources).delete()

        sources_to_add = [data_sources(name=key,display=json.dumps(value)) for key, value in inverse.items()]

        #add all new data sources
        db.session.add_all(sources_to_add)
        db.session.commit()

        print("The dictionary has " + str(len(inverse)) + " entries.")
        
        flash(f'The dictionary has {str(len(inverse))} entries.',category='info')
        line = 'Dictionary updated!'
    return render_template("meme.html",output=line)


@auth.route('/meme',methods=['GET'])
def newmeme():
    return render_template("meme.html",output='')
