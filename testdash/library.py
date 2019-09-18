import os
import platform
import time

import cpuinfo
import psutil
from Crypto.Hash import SHA512


class System:
    def __init__(self):
        # Cache
        self.processor = cpuinfo.get_cpu_info()['brand']  # Processor name (name, model, brand, clock frequency)
        self.platform = platform.system()
        self.boot_time = int(psutil.boot_time())  # Timestamp of boot

    @staticmethod
    def get_disk_info() -> list:  # Returns Disk used and total value
        return [bytes_convert(psutil.disk_usage(os.path.dirname(__file__)).used),
                bytes_convert(psutil.disk_usage(os.path.dirname(__file__)).total)]

    @staticmethod
    def get_ram_info() -> list:  # Returns RAM used and total value
        return [bytes_convert(psutil.virtual_memory().used), bytes_convert(psutil.virtual_memory().total)]

    @staticmethod
    def get_swap_info() -> list:  # Returns swap used and total value
        return [bytes_convert(psutil.swap_memory().used), bytes_convert(psutil.swap_memory().total)]

    def shutdown(self):
        if self.platform == 'Linux':
            os.system('shutdown now')
        elif self.platform == 'Windows':
            os.system('shutdown /s')
        else:
            os.system('shutdown')

    def get(self) -> dict:  # Returns all system information
        return {
            'processor': self.processor,
            'disk': self.get_disk_info(),
            'ram': self.get_ram_info(),
            'swap': self.get_swap_info(),
            'loadavg': [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()],
            'uptime': elapsed_time(self.boot_time, int(time.time())),
            'p_count': len(psutil.pids())
        }


def elapsed_time(begin: int, end: int):  # Convert time to '<hours>h <minutes>m <seconds>s' style
    elapsed = end - begin
    if elapsed // 60 > 0:
        if (elapsed // 60) // 60 > 0:
            return f'{(elapsed // 60) // 60}h {(elapsed // 60) % 60}m {(elapsed % 60) % 60}s'
        else:
            return f'{elapsed // 60}m {elapsed % 60}s'
    else:
        return f'{elapsed}s'


def bytes_convert(b: int) -> str:  # Convert bytes to Pb/Tb/Gb/Mb/Kb style
    r = ['B', 'Kb', 'Mb', 'Gb', 'Tb', 'Pb', 'Eb']
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


def check_password(password: str, password_right: str):  # Check SHA512 hash of password with original
    if SHA512.new(bytes(password, 'utf8')).digest().hex() == password_right:
        return True
    else:
        return False
