from setuptools import setup
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='ShareDB',

    # Link: https://www.python.org/dev/peps/pep-0440/#version-scheme
    version='1.0.2',

    description='''
    ShareDB is a lightweight, persistent key-value store with a dictionary-like interface
    built on top of LMDB. It is intended to replace a python dictionary when

    (1) the key-value information needs to persist locally for later reuse,
    (2) the data needs to be shared across multiple processes with minimal overhead, and
    (3) the keys and values can be (de)serialized via msgpack or pickle.

    A ShareDB instance may be opened simultaneously in children, for reading in parallel,
    while a single parent writes to the instance. Parallel writes made across processes
    are not safe; they are not guaranteed to be written, and may corrupt instance. ShareDB
    is primarily developed and tested using Linux and is compatible with both Python 2.7
    and 3.8.
    ''',

    long_description=long_description,

    long_description_content_type='text/markdown/html',

    url='https://github.com/ayaanhossain/ShareDB',

    author='Ayaan Hossain',

    # author_email='someone@somewhere.com',  # Optional

    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # These classifiers are *not* checked by 'pip install'. See instead
        # 'python_requires' below.
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='lmdb embedded key value store parallel data share read multiprocessing db',

    packages=['ShareDB'],

    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',

    install_requires=['lmdb>=0.98', 'msgpack>=0.6.2', 'configparser>=4.0.2', 'pytest-cov>=2.8.1'],

    project_urls={  # Optional
        'Bug Reports': 'https://github.com/ayaanhossain/ShareDB/issues',
        'Source'     : 'https://github.com/ayaanhossain/ShareDB/',
    },
)