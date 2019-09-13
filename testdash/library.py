import os
import time
from datetime import datetime

import cpuinfo
import psutil
from Crypto.Hash import SHA512

from . import app


class System:
    def __init__(self):
        # Cache
        self.processor = cpuinfo.get_cpu_info()['brand']
        self.boot_time = int(psutil.boot_time())

    @staticmethod
    def get_disk_info() -> list:
        return [bytes_convert(psutil.disk_usage(os.path.dirname(__file__)).used),
                bytes_convert(psutil.disk_usage(os.path.dirname(__file__)).total)]

    @staticmethod
    def get_ram_info() -> list:
        return [bytes_convert(psutil.virtual_memory().used), bytes_convert(psutil.virtual_memory().total)]

    @staticmethod
    def get_swap_info() -> list:
        return [bytes_convert(psutil.swap_memory().used), bytes_convert(psutil.swap_memory().total)]

    def get(self) -> dict:
        return {
            'processor': self.processor,
            'disk': self.get_disk_info(),
            'ram': self.get_ram_info(),
            'swap': self.get_swap_info(),
            'uptime': time_from(int(time.time()), self.boot_time)
        }


def time_from(time1: int, time2: int):
    btime = time1 - time2
    if btime // 60 > 0:
        if (btime // 60) // 60 > 0:
            return f'{(btime // 60) // 60}h {(btime // 60) % 60}m {(btime % 60) % 60}s'
        else:
            return f'{btime // 60}m {btime % 60}s'
    else:
        return f'{btime}s'


def bytes_convert(b: int) -> str:
    r = ['B', 'Kb', 'Mb', 'Gb', 'Tb', 'Pb']
    mr = 0
    while True:
        if b / 1024 > 1:
            b = b / 1024
            mr += 1
        else:
            b = round(b, 2)
            break
    return f'{b}{r[mr]}'


def encrypt_password(password: str) -> str:  # Return SHA512 hash of password
    return SHA512.new(bytes(password, 'utf8')).digest().hex()


def check_password(password: str, password_right: str):  # Checking SHA512 hash of password with original
    if SHA512.new(bytes(password, 'utf8')).digest().hex() == password_right:
        return True
    else:
        return False


@app.template_filter('timetodate')
def timestamp_to_date(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
