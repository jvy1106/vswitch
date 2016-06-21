from setuptools import setup
import sys
import os

def package_data_glob(options):
    ret = {}
    for package, path, pattern in options:
        package_path = package.replace('.', '/') + '/' 
        path = os.path.join(package_path, path)
        matches = [os.path.join(d, pattern).replace(package_path, '') for d in [x[0] for x in os.walk(path)]]
        if package not in ret:
            ret[package] = []
        ret[package].extend(matches)
    return ret

setup(name='vswitch',
    version='0.0.1',
    description='VSwitch - AWS Virtual Environment On/Off Switch',
    author='Jesse Yen',
    author_email='jesse@jads.com',
    install_requires=[
        'pyyaml',
        'boto',
        'webpyutils',
    ],
    packages=[
        'vswitch',
    ],

    package_data=package_data_glob(
        [
            ('vswitch', 'static', '*.*'),
            ('vswitch', 'templates', '*.*'),
        ]
    ),

    entry_points={'console_scripts': [
        'vswitch = vswitch.vswitch:main',
        'vswitch-server = vswitch.server:main',
    ]},
)
