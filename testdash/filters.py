from datetime import datetime
from time import time

from . import app
from .models import User

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


@app.template_filter('percent_list')
def percent_list(array: list) -> list:
    for i in range(len(array)):
        array[i] = f"{array[i]}%"
    return array


@app.template_filter('list_to_str')
def list_to_str(array: list) -> str:
    return ' '.join(array)


@app.template_filter('elapsed_time')
def elapsed_time(begin: int):  # Convert time to '<hours>h <minutes>m <seconds>s' style
    elapsed = int(time()) - int(begin)
    if elapsed // 60 > 0:
        if (elapsed // 60) // 60 > 0:
            return f'{(elapsed // 60) // 60}h {(elapsed // 60) % 60}m {(elapsed % 60) % 60}s'
        else:
            return f'{elapsed // 60}m {elapsed % 60}s'
    else:
        return f'{elapsed}s'


@app.template_filter('bytes_convert')
def bytes_convert(b: int) -> str:  # Convert bytes to Pb/Tb/Gb/Mb/Kb style
    r = ['B', 'Kb', 'Mb', 'Gb', 'Tb']
    mr = 0
    while True:
        if b / 1024 > 1:
            b = b / 1024
            mr += 1
        else:
            b = round(b, 2)
            break
    return f'{b}{r[mr]}'
