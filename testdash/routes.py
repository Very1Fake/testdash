import os
from time import time

from flask import render_template, redirect, request, flash, url_for
from flask_login import login_user, current_user, logout_user, login_required

from . import app, db, system
from . import library as lib
from .forms import SignInForm, SetupForm, NewUserForm, EditUserNameForm, EditUserPassForm, DeleteUserForm
from .models import User, Visit, Action


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
                           visits=Visit.query.order_by(Visit.timestamp.desc()).limit(5).all())


@app.route('/dashboard/users')
@login_required
def dashboard_section():  # Dashboard users page
    return render_template('dashboard/users.html', users=User.query.all())


@app.route('/dashboard/actions')
@login_required
def dashboard_action():  # Dashboard actions page
    if 'page' in request.args:
        page = int(request.args['page'])
        if page <= 0:
            flash('Хорошая попытка', 'info')
            return redirect('/dashboard')
    else:
        page = 1
    actions = Action.query.order_by(Action.timestamp.desc()).offset(20 * (page - 1)).limit(20).all()
    if len(actions) == 0:
        flash('Такой страницы не существует', 'danger')
        return redirect('/dashboard/actions?page=1')
    elif len(Action.query.order_by(Action.timestamp.desc()).offset(20 * page).limit(20).all()) == 0:
        page_next = False
    else:
        page_next = True
    return render_template('dashboard/actions.html', actions=actions, next=page_next, page=page)


@app.route('/dashboard/visits')
@login_required
def dashboard_visits():  # Dashboard visits page
    if 'page' in request.args:
        page = int(request.args['page'])
        if page <= 0:
            flash('Хорошая попытка', 'info')
            return redirect('/dashboard')
    else:
        page = 1
    visits = Visit.query.order_by(Visit.timestamp.desc()).offset(30 * (page - 1)).limit(30).all()
    if len(visits) == 0:
        flash('Такой страницы не существует', 'danger')
        return redirect('/dashboard/visits?page=1')
    elif len(Visit.query.order_by(Visit.timestamp.desc()).offset(30 * page).limit(30).all()) == 0:
        page_next = False
    else:
        page_next = True
    return render_template('dashboard/visits.html', visits=visits, next=page_next, page=page)


@app.route('/action')
@login_required
def actions():
    return redirect('/dashboard/actions')


@app.route('/action/see/<int:action_id>')
def action_see(action_id):
    action = Action.query.filter_by(id=action_id).first()
    if action:
        return render_template('action/see.html', action=action)
    else:
        flash('Данного действия не существует', 'danger')
        return redirect('/dashboard/actions')


@app.route('/user')
@login_required
def users():
    return redirect('/dashboard/users')


@app.route('/user/new', methods=['GET', 'POST'])
@login_required
def user_new():
    form = NewUserForm(request.form)
    if form.validate_on_submit():
        if not User.query.filter_by(login=form.login.data).first():
            user = User(login=form.login.data, name=form.name.data, password=lib.encrypt_password(form.password.data),
                        timestamp=time())
            db.session.add(
                Action(name='user_create', login=current_user.login, address=request.remote_addr, timestamp=time(),
                       comment=f"Создание пользователя '{user.login}'"))
            db.session.add(user)
            db.session.commit()
            flash(f"Пользователь '{form.login.data}' успешно создан", 'success')
            return redirect('/dashboard/users')
        else:
            flash(f"Пользователь '{form.login.data}' уже существует", 'danger')
            return redirect('/dashboard/users')
    return render_template('user/new.html', form=form)


@app.route('/user/edit/<login>', methods=['GET', 'POST'])
@login_required
def user_edit(login):
    form_name = EditUserNameForm(request.form)
    form_pass = EditUserPassForm(request.form)
    user = User.query.filter_by(login=login).first()
    if not user:
        flash(f"Пользователя '{login}' не существует", 'danger')
        return redirect('/dashboard/users')
    if form_pass.validate_on_submit():
        user.password = lib.encrypt_password(form_pass.password.data)
        db.session.add(
            Action(name='user_edit_password', login=current_user.login, address=request.remote_addr, timestamp=time(),
                   comment=f"Именение пароля пользователя '{user.login}'"))
        db.session.add(user)
        db.session.commit()
        flash(f"Пароль пользователя '{user.login}' успешно изменён", 'success')
        return redirect('/dashboard/users')
    elif form_name.validate_on_submit():
        db.session.add(
            Action(name='user_edit_name', login=current_user.login, address=request.remote_addr, timestamp=time(),
                   comment=f"Именение имени пользователя '{user.login}' с '{user.name}' на '{form_name.name.data}'"))
        user.name = form_name.name.data
        db.session.add(user)
        db.session.commit()
        flash(f"Имя пользователя '{user.login}' успешно изменено", 'success')
        return redirect('/dashboard/users')
    return render_template('user/edit.html', user=user, form_name=form_name, form_pass=form_pass)


@app.route('/user/delete/<login>', methods=['GET', 'POST'])
@login_required
def user_delete(login):
    form = DeleteUserForm(request.form)
    user = User.query.filter_by(login=login).first()
    if not user:
        flash(f"Пользователя '{login}' не существует", 'danger')
    if form.validate_on_submit():
        if form.login.data == user.login:
            db.session.add(
                Action(name='user_delete', login=current_user.login, address=request.remote_addr, timestamp=time(),
                       comment=f"Удаление пользователя '{user.login}'"))
            Visit.query.filter_by(login=user.login).delete()
            Action.query.filter_by(login=user.login).delete()
            db.session.delete(user)
            db.session.commit()
            flash(f"Пользователь '{user.login}' удалён", 'info')
            return redirect('/dashboard/users')
        else:
            flash('Вы неправильно ввели логин пользователя', 'danger')
    return render_template('user/delete.html', form=form, user=user.login)


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    form = SetupForm(request.form)
    if form.validate_on_submit():
        db.session.add(
            Action(name='setup', login='<SYSTEM>', address='', timestamp=time(), comment='Установка завершена'))
        user = User(login=form.login.data, name=form.name.data, password=lib.encrypt_password(form.password.data),
                    timestamp=time())
        db.session.add(Action(name='user_create', login='<SYSTEM>', address='', timestamp=time(),
                              comment=f"Создание пользователя '{user.login}'"))
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
