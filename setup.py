# coding: utf-8
from setuptools import setup


__version__ = None
exec(open('scotty/version.py').read())


def next_version():
    _v = __version__.split('.')
    _v[-1] = str(int(_v[-1]) + 1)
    return '.'.join(_v)


def read_file(f):
    try:
        with open(f, 'r') as _file:
            return _file.read()
    except Exception:
        return ''

setup(
    name='Scotty',
    version=__version__,
    url='https://github.com/laco/python-scotty/',
    download_url='https://github.com/laco/python-scotty/tarball/' + __version__,
    license='Apache2.0',
    author='László Andrási',
    author_email='mail@laszloandrasi.com',
    description='AWS ECS Container Deployment Tool',
    long_description=read_file('README.md') + '\n\n',
    packages=['scotty'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=['Click', 'PyYAML', 'jinja2', 'boto3'],
    entry_points="""
       [console_scripts]
       scotty=scotty:main
    """,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
