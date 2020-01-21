<h1 align="center">
    <img src="./logo/logo.svg"  alt="ShareDB" width="250"/>
</h1>

<p align="center">
	<a href="https://img.shields.io/badge/version-0.1.6-blue">
	    <img src="https://img.shields.io/badge/version-0.1.6-blue"
	     alt="version-badge">
    </a>
	<a href="https://github.com/ayaanhossain/ShareDB/workflows/CI/badge.svg">
	    <img src="https://github.com/ayaanhossain/ShareDB/workflows/CI/badge.svg"
	     alt="CI-badge">
    </a>
	<a href="https://codecov.io/github/ayaanhossain/ShareDB/coverage.svg?branch=master">
	    <img src="https://codecov.io/github/ayaanhossain/ShareDB/coverage.svg?branch=master"
	     alt="codecov-badge">
    </a>
	<a href="https://img.shields.io/badge/python-2.7%20and%203.8-blue">
	    <img src="https://img.shields.io/badge/python-2.7%20and%203.8-blue"
	     alt="python-badge">
    </a>
	<a href="https://img.shields.io/badge/os-Linux-blue">
	    <img src="https://img.shields.io/badge/os-Linux-blue"
	     alt="os-badge">
    </a>
</p>

<p align="center">
  <a href="#sharedb-in-action">ShareDB in Action</a> •
  <a href="#installation">Installation</a> •
  <a href="#license">License</a> •
  <a href="#contribution">Contribution</a> •
  <a href="#api">API</a>
</p>

`ShareDB` is a lightweight, **persistent key-value store** with a **dictionary-like interface** built on top of [LMDB](https://symas.com/lmdb/). It is intended to replace a python dictionary when

 1. the key-value store needs to **persist locally** for later reuse,
 2. the data needs to be **read across multiple processes** with minimal overhead, and 
 3. the **keys** and **values** can be (de)serialized via **msgpack** or **pickle**.

Sending a `ShareDB` object to children processes is fine, or you may open the same `ShareDB` instance in parellel for reading. **Parallel writes made in children processes are not safe**; they are not guaranteed to be written, and may corrupt instance. `ShareDB` is primarily developed and tested using **Linux** and is compatible with both **Python 2.7 and 3.8**.

### `ShareDB` in Action
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

### Installation
One-shot **installation/upgrade** of `ShareDB` from **PyPI**
```bash
$ pip install ShareDB --upgrade
```
Alternatively, **clone** `ShareDB` from **GitHub**
```bash
$ git clone github.com/ayaanhossain/ShareDB
```
`ShareDB` requires the following additional libraries
- [lmdb](https://pypi.org/project/lmdb/) >= 0.98
- [msgpack](https://pypi.org/project/msgpack/) >= 0.6.2
- [configparser](https://pypi.org/project/configparser/) >= 4.0.2
- [pytest](https://pypi.org/project/pytest/) >= 4.6.9

You can install all of the **dependencies** from **requirements.txt**
```bash
$ cd ShareDB
$ pip install -r requirements.txt
```
Or, you can **install** all dependencies and `ShareDB`
```bash
$ python setup.py install
```
Finally, **test** your `ShareDB` installation with **pytest**
```bash
$ pytest
```
**Uninstallation** of `ShareDB` is easy with `pip`
```bash
$ pip uninstall ShareDB
```

### License

### Contribution

### API

