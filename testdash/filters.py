from datetime import datetime

from .models import User
from . import app


''' Filters for jinja '''


@app.template_filter('time_to_date')
def timestamp_to_date(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


@app.template_filter('get_user_name')
def get_user_name(login: str) -> str:
    name = User.query.filter_by(login=login).first().name
    if name == '':
        return login
    else:
        return name


@app.template_filter('user_mention')
def user_mention(login: str) -> str:
    if login != '<SYSTEM>':
        return f'<a href="/user/edit/{login}" class="badge badge-pill badge-info">{login}</a>'
    else:
        return '&#60;SYSTEM&#62;'
