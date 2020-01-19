<h1 align="center">
    <img src="./logo/logo.svg"  alt="ShareDB" width="250"/>
</h1>

<p align="center">
	[s/w version]
	<a href="https://github.com/ayaanhossain/ShareDB/workflows/CI/badge.svg">
	    <img src="https://github.com/ayaanhossain/ShareDB/workflows/CI/badge.svg"
	     alt="CI-Badge">
    </a>
	[codecov]
	[python]
	[os versions]
</p>

ShareDB is a lightweight, **persistent key-value store** with a **dictionary-like interface** built on top of [LMDB](https://symas.com/lmdb/). It is intended to replace a python dictionary when

 1. the key-value store needs to **persist locally** for later reuse,
 2. the data needs to be **read across multiple processes** with minimal overhead, and 
 3. the **keys and values** can be (de)serialized via **msgpack or cPickle**.

Sending a ShareDB object to children processes is fine, or you may open the same ShareDB instance in parellel for reading. **Parallel writes made in children processes are not safe**; they are not guaranteed to be written, and may corrupt instance. ShareDB is primarily developed and tested using **Linux** and is compatible with both **Python 2.7 and 3.4+**.

### Table of Contents
 * [ShareDB in Action](#sharedb-in-action)
 * [Requirements](#requirements)
 * [Installation](#installation)
 * [Testing](#testing)
 * [License](#license)
 * [Contribution](#contribution)
 * [Usage ](#usage)
 * [Acknowledgement ](#acknowledgement)

### ShareDB in Action
```python
>>> from ShareDB import ShareDB           # Easy import
>>> print(ShareDB.__version__)            # Check version
0.1.6
>>> myDB = ShareDB(path='./test.ShareDB') # Store ShareDB locally
>>> myDB['Name'] = ['Ayaan Hossain']      # Insert information
>>> myDB.get(key='Name')                  # Retrieve values
['Ayaan Hossain']
>>> # Pythonic insertion/update of multiple items
>>> len(myDB.multiset(kv_iter=zip(range(0, 10), range(10, 20))).sync())
11
>>> 7 in myDB                             # Membership queries work
True
>>> myDB['non-existent key']              # KeyError on invalid get as expected
Traceback (most recent call last):
...
KeyError: "key=non-existent key of <type 'str'> is absent"
>>> myDB.pop(7)                           # Pop a key just like a dictionary
17
>>> list(myDB.multipopitem(num_items=5))  # Or, pop as many items as you need
[(0, 10), (1, 11), (2, 12), (3, 13), (4, 14)]
>>> myDB.remove(5).length()               # Remove a single key
4
>>> myDB.clear().length()                 # Or, clear entire ShareDB
0
>>> myDB.drop()                           # Close/delete when you're done
True
```

### Requirements
Apart from the standard library, ShareDB requires the following to run:

 - [lmdb](https://pypi.org/project/lmdb/) >= 0.98
 - [msgpack](https://pypi.org/project/msgpack/) >= 0.6.2

### Installation

### Testing

### License

### Contribution

### Usage

### Acknowledgement

