"""
Flask-Monitor
-------------

This is the description for that library
"""
import os
from setuptools import setup, find_packages

__version__ = '2.0'
__desc__ = "Flask Task Monitor module"
__urlpkg__ = "http://github.com/nonetheless/Flask-Task-Monitor.git"


def walk_path_files(directory, target_folder=None):
    res = {}
    for subdir, dir, files in os.walk(directory):
        if target_folder is not None:
            target = os.path.join(target_folder, subdir)
        else:
            target = subdir
        if target not in res:
            res[target] = []
        for fname in files:
            res[target].append(os.path.join(subdir, fname))
    return res


HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'README.rst')) as readme:
        LONG_DESC = readme.read()

data_files = []

requirements = open(os.path.join(os.path.dirname(__file__), 'requirements.txt')).readlines()
install_requires = [i.strip('\r\n ') for i in requirements]
setup(
    name='Flask-Task-Monitor',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    data_files=data_files,
    url='http://github.com/nonetheless/Flask-Task-Monitor',
    license='MIT',
    author='nonetheless',
    author_email='',
    description=__desc__,
    long_description=LONG_DESC,
    install_requires=install_requires,
    keywords=['utility', 'versioning'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
