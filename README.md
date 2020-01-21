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
	<a href="https://codecov.io/gh/ayaanhossain/ShareDB">
		<img src="https://codecov.io/gh/ayaanhossain/ShareDB/branch/master/graph/badge.svg?token=syTKRG9H8O"
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
  <a href="#contributing">Contributing</a> •
  <a href="#acknowledgements">Acknowledgements</a> •
  <a href="./API.md">API</a>
</p>

`ShareDB` is a lightweight, **persistent key-value store** with a **dictionary-like interface** built on top of [LMDB](https://symas.com/lmdb/). It is intended to replace a python dictionary when

 1. the key-value store needs to **persist locally** for later reuse,
 2. the data needs to be **read across multiple processes** with minimal overhead, and 
 3. the **keys** and **values** can be (de)serialized via **msgpack** or **pickle**.

Sending a `ShareDB` object to children processes is fine, or you may open the same `ShareDB` instance in parallel for reading. **Parallel writes made in children processes are not safe**; they are not guaranteed to be written, and may corrupt instance. `ShareDB` is primarily developed and tested using **Linux** and is compatible with both **Python 2.7 and 3.8**.

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
>>> myDB.remove(5).remove(6).remove(7).length()               # Chain removal of several keys
1
>>> myDB.clear().length()                 # Or, clear entire ShareDB
0
>>> myDB.drop()                           # Close/delete when you're done
True
```
`ShareDB` operates mostly like an idiomatic Python dictionary. Most methods either return some data/result up on appropriate query, or a `self` object is returned for pythonic chaining of methods. Exceptionally, the *terminal* methods `.close()` and `.drop()` return a boolean indicating success of their operations.

### Installation
One-shot **installation/upgrade** of `ShareDB` from **PyPI**
```bash
$ pip install ShareDB --upgrade
```
Alternatively, **clone** `ShareDB` from **GitHub** locally
```bash
$ git clone github.com/ayaanhossain/ShareDB
```
`ShareDB` requires the following additional libraries
- [lmdb](https://pypi.org/project/lmdb/) >= 0.98
- [msgpack](https://pypi.org/project/msgpack/) >= 0.6.2
- [configparser](https://pypi.org/project/configparser/) >= 4.0.2
- [pytest](https://pypi.org/project/pytest/) >= 4.6.9

You can **install** all **dependencies** from **requirements.txt** inside `/ShareDB/` directory
```bash
$ cd ShareDB
$ pip install -r requirements.txt
```
Or, you can directly **install** all **dependencies** and `ShareDB` via `setup.py`
```bash
$ python setup.py install
```
You can **test** `ShareDB` installation with **pytest** inside `/ShareDB/tests/` directory
```bash
$ cd tests
$ pytest
```
**Uninstallation** of `ShareDB` is easy with `pip`
```bash
$ pip uninstall ShareDB
```

### License
`ShareDB` (c) 2019-2020 Ayaan Hossain.

`ShareDB` is an **open-source software** under [MIT](https://opensource.org/licenses/MIT) License.

See [LICENSE](./LICENSE) file for more details.

### Contributing
We recommend **discussing** any changes you have in mind by first **opening an issue**.

To contribute to `ShareDB`, please **clone** or **fork** this repository, **commit** your code on a **separate branch**, and **submit** a **pull request** following the [Contributor Covenant](https://www.contributor-covenant.org/version/2/0/code_of_conduct). See [COC.md](./docs/COC.md) file for more details.

Please ensure that **all code modifications** are accompanied by detailed **comments**, **new unit tests** as reasonable, and **pass existing unit tests**.  For versioning, we use [SemVer](https://semver.org/).

### Acknowledgements
`ShareDB` is maintained by:

 - Ayaan Hossain | [github.com/ayaanhossain](https://github.com/ayaanhossain) | [@bioalgorithmist](https://twitter.com/bioalgorithmist)

`ShareDB` was primarily developed by Ayaan to meet scalable data analytics needs at [Prof. Howard Salis](https://twitter.com/hsalis)' Lab at [Penn State University](https://salislab.net/).

Prof. Salis has funded the initial development of `ShareDB`.

### API
`ShareDB` API details can be found in the [API.md](./docs/API.md) file.
