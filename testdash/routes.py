import os
import subprocess
from time import time

import psutil
from flask import render_template, redirect, request, flash, url_for, session, Response
from flask_login import login_user, current_user, logout_user, login_required

from . import app, db, system
from . import library as lib
from .forms import SignInForm, SetupForm, NewUserForm, EditUserNameForm, EditUserPassForm, DeleteUserForm, \
    ExecuteCommandForm, ConfirmForm
from .models import User, Visit, Action


@app.before_request
def preload():  # Checking for db state (will be deprecated soon)
    if not os.path.exists('app.db'):
        db.create_all()
    if not User.query.first():
        if request.endpoint != 'setup' and request.endpoint != 'static':
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
def dashboard_actions():  # Dashboard actions page
    if 'page' in request.args:
        page = int(request.args['page'])
        if page <= 0:
            flash('Хорошая попытка', 'info')
            return redirect('/dashboard')
    else:
        page = 1
    action_list = Action.query.order_by(Action.timestamp.desc()).offset(20 * (page - 1)).limit(20).all()
    if len(action_list) == 0:
        flash('Такой страницы не существует', 'danger')
        return redirect('/dashboard/actions?page=1')
    elif len(Action.query.order_by(Action.timestamp.desc()).offset(20 * page).limit(20).all()) == 0:
        page_next = False
    else:
        page_next = True
    return render_template('dashboard/actions.html', actions=action_list, next=page_next, page=page)


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


@app.route('/dashboard/tools')
@login_required
def dashboard_tools():
    form = ConfirmForm()
    return render_template('dashboard/tools.html', form=form)


@app.route('/action')
@login_required
def actions():
    return redirect('/dashboard/actions')


@app.route('/action/see/<int:action_id>')
@login_required
def action_see(action_id):
    action = Action.query.filter_by(id=action_id).first()
    if action:
        return render_template('action/see.html', action=action)
    else:
        flash('Данного действия не существует', 'danger')
        return redirect('/dashboard/actions')


@app.route('/tool')
@login_required
def tools():
    return redirect('/dashboard')


@app.route('/tool/cpu_usage')
@login_required
def tool_processor_usage():
    return render_template('tool/cpu_usage.html', cpu_usage=psutil.cpu_times_percent()._asdict())


@app.route('/tool/exec', methods=['GET', 'POST'])
@login_required
def tool_exec():
    form = ExecuteCommandForm(request.form)
    if form.validate_on_submit():
        session['exec_cmd'] = form.command.data
        session['exec_dir'] = form.directory.data if form.directory.data else '/'
        session['exec_timeout'] = form.timeout.data
        return redirect('/tool/exec_output')
    return render_template('tool/exec.html', form=form)


@app.route('/tool/exec_output')
@login_required
def tool_exec_output():
    command = session.get('exec_cmd', None)
    directory = session.get('exec_dir', None)
    timeout = session.get('exec_timeout', None)
    if command and directory and timeout:
        db.session.add(Action(name='exec', login=current_user.login, address=request.remote_addr, timestamp=time(),
                              comment=f"Команда: {command}\nДиректория: {directory}\nТаймаут: {timeout}"))
        db.session.commit()
        try:
            result = subprocess.run(command, timeout=timeout, cwd=directory, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
        except subprocess.TimeoutExpired:
            return Response(f'COMMAND: {command}\nDIRECTORY: {directory}\nOUTPUT:\nВремя ожидания истекло',
                            mimetype='text/text')
        else:
            session.pop('exec_cmd')
            session.pop('exec_dir')
            session.pop('exec_timeout')
            text = f"COMMAND: {command}\nDIRECTORY: {directory}\n"
            try:
                if result.stdout:
                    text += f"OUTPUT:\n{result.stdout.decode('utf8')}"
                if result.stderr:
                    text += f"ERRORS:\n{result.stderr.decode('utf8')}"
            except UnicodeDecodeError:
                if result.stdout:
                    text += f"OUTPUT:\n{result.stdout}"
                if result.stderr:
                    text += f"ERRORS:\n{result.stderr}"
            finally:
                return Response(text, mimetype='text/text')
    else:
        return redirect('/tool/exec')


@app.route('/tool/process/<int:pid>')
@login_required
def tool_process(pid: int):
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        flash(f'Процесса #{pid} не существует', 'danger')
        return redirect('/dashboard/tools')
    else:
        return render_template('tool/process.html', process=process)


@app.route('/tool/process_kill/<int:pid>')
@login_required
def tool_process_kill(pid: int):
    try:
        process = psutil.Process(pid)
        comment = f'PID: {process.pid}\nИмя: {process.name()}\nПользователь: ' \
                  f'{process.username()}\nКоманда: {" ".join(process.cmdline())}'
        process.kill()
    except psutil.NoSuchProcess:
        flash(f'Процесса #{pid} не существует', 'danger')
        return redirect('/dashboard/tools')
    else:
        db.session.add(
            Action(name='process_kill', login=current_user.login, address=request.remote_addr, timestamp=time(),
                   comment=comment))
        db.session.commit()
        flash(f'Процесс #{pid} завершён', 'info')
        return redirect('/dashboard/tools')


@app.route('/tool/process_list')
@login_required
def tool_process_list():
    return render_template('tool/process_list.html', p_list=psutil.process_iter())


@app.route('/tool/reset', methods=['GET', 'POST'])
@login_required
def tool_reset():
    form = ConfirmForm(request.form)
    if form.validate_on_submit():
        if lib.encrypt_password(form.confirmation.data) == User.query.filter_by(id=current_user.id).first().password:
            db.drop_all()
            db.create_all()
            db.session.add(Action(name='reset', login='<SYSTEM>', address='', timestamp=time(),
                                  comment=f'Сброс данный панели управления пользователем "{current_user.login}".' +
                                          f' С "{request.remote_addr}"'))
            db.session.commit()
        else:
            flash('Введён неверный пароль', 'danger')
            db.session.add(
                Action(name='reset_attempt', login=current_user.login, address=request.remote_addr, timestamp=time(),
                       comment=''))
            db.session.commit()
            return redirect('/dashboard/tools')
    return redirect('/')


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
    else:
        if user.login == current_user.login:
            pass_allowed = True
        else:
            pass_allowed = False
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
        if user.login != current_user.login:
            flash(f'Вы не можете изменить пароль другому пользователю', 'danger')
            return redirect('/dashboard/users')
        db.session.add(
            Action(name='user_edit_name', login=current_user.login, address=request.remote_addr, timestamp=time(),
                   comment=f"Именение имени пользователя '{user.login}' с '{user.name}' на '{form_name.name.data}'"))
        user.name = form_name.name.data
        db.session.add(user)
        db.session.commit()
        flash(f"Пароль успешно изменено", 'success')
        return redirect('/dashboard/users')

    return render_template('user/edit.html', user=user, form_name=form_name, form_pass=form_pass,
                           pass_allowed=pass_allowed)


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


@app.route('/server/shutdown', methods=['GET', 'POST'])
@login_required
def server_shutdown():  # Shutdown server
    form = ConfirmForm(request.form)
    if form.validate_on_submit() and \
            lib.encrypt_password(form.confirmation.data) == User.query.filter_by(id=current_user.id).first().password:
        db.session.add(Action(name='shutdown', login=current_user.login, address=request.remote_addr, timestamp=time(),
                              comment=''))
        db.session.commit()
        system.shutdown()
    else:
        flash('Введён неверный пароль', 'danger')
        db.session.add(
            Action(name='shutdown_attempt', login=current_user.login, address=request.remote_addr, timestamp=time(),
                   comment=''))
        db.session.commit()
        return redirect('/dashboard/tools')


@app.route('/setup', methods=['GET', 'POST'])
def setup():  # Setup page
    if User.query.first():
        return redirect('/')
    form = SetupForm(request.form)
    if form.validate_on_submit():
        db.session.add(
            Action(name='setup', login='<SYSTEM>', address='', timestamp=time(), comment='Установка завершена'))
        user = User(login=form.login.data, name=form.name.data, password=lib.encrypt_password(form.password.data),
                    timestamp=time())
        db.session.add(Action(name='user_create', login='<SYSTEM>', address='', timestamp=time(),
                              comment=f"Создание пользователя '{user.login}'"))
        db.session.add(Visit(login=user.login, address=request.remote_addr, timestamp=time()))
        db.session.add(user)
        db.session.commit()
        flash(f'Установка успешна завершена', 'info')
        flash(f"Пользователь '{form.login.data}' создан", 'success')
        login_user(user, remember=False)
        return redirect('/')
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
def error404(error):  # Error 404 page
    return render_template('404.html')
