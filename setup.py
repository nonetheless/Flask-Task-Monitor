"""
Flask-Monitor
-------------

This is the description for that library
"""
import os
from setuptools import setup, find_packages

__version__ = '1.0'


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


data_files = []

requirements = open(os.path.join(os.path.dirname(__file__), 'requirements.txt')).readlines()
install_requires = [i.strip('\r\n ') for i in requirements]
setup(
    name='Flask-Monitor',
    version='1.0',
    url='http://example.com/flask-monitor/',
    license='BSD',
    author='Your Name',
    author_email='your-email@example.com',
    description='Very short description',
    long_description=__doc__,
    py_modules=['flask_monitor'],
    # if you would be using a package instead use packages instead
    # of py_modules:
    # packages=['flask_monitor'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

setup(
    name='Flask-Monitor',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    data_files=data_files,
    url='http://github.com/nonetheless/flask-monitor',
    license='',
    author='nonetheless',
    author_email='',
    description='flask monitor plugin',
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