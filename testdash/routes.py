import os
from time import time

from flask import render_template, redirect, request, flash, url_for, abort
from flask_login import login_user, current_user, logout_user, login_required

from . import app, db, system
from . import library as lib
from .forms import SignInForm, SetupForm, NewUserForm, EditUserNameForm, EditUserPassForm
from .models import User, Visit


@app.before_request
def preload():  # Checking for db state (will be deprecated soon)
    if not os.path.exists('app.db'):
        db.create_all()
    if not User.query.first():
        if not request.endpoint == 'setup':
            return redirect('/setup')


@app.route('/')
def main():  # Redirect to page by auth state
    if current_user.is_authenticated:
        return redirect('/dashboard')
    return redirect('/signin')


@app.route('/dashboard')
@login_required
def dashboard():  # Dashboard main section
    return render_template('dashboard/main.html', sys_info=system.get(),
                           visits=Visit.query.order_by(Visit.id.desc()).limit(5).all())


@app.route('/dashboard/<section>')
@login_required
def dashboard_section(section):  # Dashboard section
    if section == 'main':
        return redirect('/dashboard')
    elif section == 'users':
        return render_template('dashboard/users.html', users=User.query.all())
    else:
        return abort(404)


@app.route('/user')
def users(action):
    return redirect('/dashboard/users')


@app.route('/user/new', methods=['GET', 'POST'])
def user_new():
    form = NewUserForm(request.form)
    if form.validate_on_submit():
        if not User.query.filter_by(login=form.login.data).first():
            user = User(login=form.login.data, name=form.name.data, password=lib.encrypt_password(form.password.data),
                        timestamp=time())
            db.session.add(user)
            db.session.commit()
            flash(f"Пользователь '{form.login.data}' успешно создан", 'success')
            return redirect('/dashboard/users')
        else:
            flash(f"Пользователь '{form.login.data}' уже существует", 'danger')
            return redirect('/dashboard/users')
    return render_template('user/new.html', form=form)


@app.route('/user/edit/<login>', methods=['GET', 'POST'])
def user_edit(login):
    form_name = EditUserNameForm(request.form)
    form_pass = EditUserPassForm(request.form)
    user = User.query.filter_by(login=login).first()
    if not user:
        flash(f"Пользователя '{login}' не существует", 'danger')
        return redirect('/dashboard/users')
    if form_pass.validate_on_submit():
        user = User.query.filter_by(login=login).first()
        user.password = lib.encrypt_password(form_pass.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"Пароль пользователя '{user.login}' успешно изменён", 'success')
        return redirect('/dashboard/users')
    elif form_name.validate_on_submit():
        user = User.query.filter_by(login=login).first()
        user.name = form_name.name.data
        db.session.add(user)
        db.session.commit()
        flash(f"Имя пользователя '{user.login}' успешно изменено", 'success')
        return redirect('/dashboard/users')
    return render_template('user/edit.html', user=user, form_name=form_name, form_pass=form_pass)


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    form = SetupForm(request.form)
    if form.validate_on_submit():
        user = User(login=form.login.data, name=form.name.data, password=lib.encrypt_password(form.password.data),
                    timestamp=time())
        db.session.add(user)
        db.session.commit()
        flash(f'Установка успешна завершена', 'info')
        flash(f"Пользователь '{form.login.data}' создан", 'success')
        return redirect('/signin')
    return render_template('setup.html', form=form)


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
