from setuptools import setup, find_packages
from os import path
from io import open

import ShareDB

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='ShareDB',
    
    # Link: https://www.python.org/dev/peps/pep-0440/#version-scheme
    version=ShareDB.__version__,
    
    description='Pythonic key-value store based on LMDB for parallel-read workflows.',
    
    long_description=long_description,
    
    long_description_content_type='text/markdown',
    
    url='https://github.com/ayaanhossain/ShareDB',
    
    author=ShareDB.__author__,
    
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
    ],
    keywords='LMDB key-value store parallel data share',

    packages=['ShareDB'],

    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',

    install_requires=['lmdb', 'msgpack'],

    project_urls={  # Optional
        'Bug Reports': 'https://github.com/pypa/sampleproject/issues',
        'Source'     : 'https://github.com/pypa/sampleproject/',
    },
)