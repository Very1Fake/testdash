import os
from time import time

from flask import render_template, redirect, request, flash, url_for, abort
from flask_login import login_user, current_user, logout_user, login_required

from .models import User, Visit
from .forms import SignInForm
from . import library as lib
from . import app, db, system


@app.before_request
def preload():  # Checking for db state (will be deprecated soon)
    if not os.path.exists('app.db'):
        db.create_all()
    if not User.query.first():
        db.session.add(User(login="root", password=lib.encrypt_password('root'), timestamp=time()))
        db.session.commit()


@app.route('/')
def main():  # Redirect to page by auth state
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('signin'))


@app.route('/dashboard')
@login_required
def dashboard():  # Dashboard main section
    return render_template('dashboard/main.html', sys_info=system.get(), visits=Visit.query.order_by(Visit.id.desc()).limit(5).all())


@app.route('/dashboard/<section>')
def dashboard_section(section):  # Dashboard section
    if section == 'main':
        return redirect(url_for('dashboard'))
    elif section == 'users':
        return render_template('dashboard/users.html', users=User.query.all())
    else:
        return abort(404)


'''@app.route('/setup', methods=['GET', 'POST'])
def setup():
    print(1)
    form = SetupForm(request.form)
    if form.validate_on_submit():
        print(2)
        print(User(login=form.login.data).set_password(form.password.data))
        flash(f'Установка успешна завершена', 'info')
        flash(f"Пользователь '{form.login.data}' создан", 'success')
        return redirect('/signin')
    print(3)
    return render_template('setup.html', form=form)'''


@app.route('/signin', methods=['GET', 'POST'])
def signin():  # Auth page
    if current_user.is_authenticated:
        return redirect('/')
    form = SignInForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(login=form.login.data).first()
        if user and lib.check_password(form.password.data, user.password):
            db.session.add(Visit(login=user.login, address=request.remote_addr, timestamp=time()))
            db.session.commit()
            login_user(user, remember=form.remember.data)
            return redirect(request.args.get('next')) if request.args.get('next') else redirect(url_for('dashboard'))
        flash('Логин или пароль введены неверно', 'danger')
    return render_template('signin.html', form=form)


@app.route('/signout')
@login_required
def signout():  # Sign out page
    logout_user()
    return redirect('/')


@app.errorhandler(404)
def error404(e):
    return render_template('404.html')
