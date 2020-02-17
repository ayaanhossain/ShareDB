<h1 align="center">
	<a href="https://github.com/ayaanhossain/ShareDB/">
		<img src="./logo/logo.svg"  alt="ShareDB" width="250"/>
    </a>
</h1>

<p align="center">
	<a href="https://github.com/ayaanhossain/ShareDB/actions">
	    <img src="https://github.com/ayaanhossain/ShareDB/workflows/build/badge.svg"
	     alt="CI-badge">
    </a>
	<a href="https://codecov.io/gh/ayaanhossain/ShareDB">
		<img src="https://codecov.io/gh/ayaanhossain/ShareDB/branch/master/graph/badge.svg?token=syTKRG9H8O"
		 alt="codecov-badge">
    </a>
	<a href="https://img.shields.io/badge/version-0.1.6-blue">
		<img src="https://img.shields.io/badge/version-0.1.6-blue"
		 alt="version-badge">
	</a>
	<a href="https://img.shields.io/badge/python-2.7%20%7C%203.8-blue">
	    <img src="https://img.shields.io/badge/python-2.7%20%7C%203.8-blue"
	     alt="python-badge">
    </a>
    <a href="https://img.shields.io/badge/os-Linux-9cf">
	    <img src="https://img.shields.io/badge/os-Linux-9cf"
	     alt="os-badge">
    </a>
	<a href="./LICENSE">
	    <img src="https://img.shields.io/badge/license-MIT-yellow"
	     alt="license-badge">
    </a>
</p>

<p align="center">
  <a href="#sharedb-in-action">ShareDB in Action</a> •
  <a href="#installation">Installation</a> •
  <a href="#license">License</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#acknowledgements">Acknowledgements</a> •
  <a href="./docs/API.md">API</a>
</p>

`ShareDB` is a lightweight, **persistent key-value store** with a **dictionary-like interface** built on top of [LMDB](https://symas.com/lmdb/). It is intended to replace a python dictionary when

 1. the key-value store needs to **persist locally** for later reuse,
 2. the data needs to be **read across multiple processes** with minimal overhead, and 
 3. the **keys** and **values** can be (de)serialized via **msgpack** or **pickle**.

A `ShareDB` instance may be opened simultaneously in children, for reading in parallel, while a single parent writes to the instance. **Parallel writes made across processes are not safe**; they are not guaranteed to be written, and may corrupt instance. `ShareDB` is primarily developed and tested using **Linux** and is compatible with both **Python 2.7 and 3.8**.

### `ShareDB` in Action
```python
>>> from ShareDB import ShareDB           # Easy import
>>> print(ShareDB.__version__)            # Check version
0.4.5
>>> myDB = ShareDB(path='./test.ShareDB') # Store ShareDB locally
>>> myDB['Name'] = ['Ayaan Hossain']      # Insert information
>>> myDB.get(key='Name')                  # Retrieve values
['Ayaan Hossain']
>>> # Accelerated batch insertion/update via a single transaction
>>> len(myDB.multiset(kv_iter=zip(range(0, 10), range(10, 20))).sync())
11
>>> 7 in myDB                             # Membership queries work
True
>>> myDB['non-existent key']              # KeyError on invalid get as expected
Traceback (most recent call last):
...
KeyError: "key=non-existent key of <class 'str'> is absent"
>>> myDB.pop(7)                           # Pop a key just like a dictionary
17
>>> list(myDB.multipopitem(num_items=5))  # Or, pop as many items as you need
[(0, 10), (1, 11), (2, 12), (3, 13), (4, 14)]
>>> myDB.remove(5).remove(6).length()     # Chain removal of several keys
2
>>> myDB.clear().length()                 # Or, clear entire ShareDB
0
>>> myDB.drop()                           # Close/delete when you're done
True
```
`ShareDB` methods either return data/result up on appropriate query, or a `self` object is returned to facilitate method chaining. Terminal methods `.close()` and `.drop()` return a boolean indicating success.

Please checkout the `/examples/` directory for a complete example of using `ShareDB`.  Please checkout the [API.md](./docs/API.md) file for API details.

### Installation
One-shot **installation/upgrade** of `ShareDB` from **PyPI**
```bash
$ pip install --upgrade ShareDB
```
Alternatively, **clone** `ShareDB` from **GitHub**
```bash
$ git clone https://github.com/ayaanhossain/ShareDB
```
`ShareDB` requires the following additional libraries
- [lmdb](https://pypi.org/project/lmdb/) >= 0.98
- [msgpack](https://pypi.org/project/msgpack/) >= 0.6.2
- [configparser](https://pypi.org/project/configparser/) >= 4.0.2
- [pytest-cov](https://pypi.org/project/pytest-cov/) >= 2.8.1

You can **install** all **dependencies** from **requirements.txt** inside `/ShareDB/` directory
```bash
$ cd ShareDB
$ pip install -r requirements.txt
```
Or, you can directly **install** all **dependencies** and `ShareDB` via `setup.py`
```bash
$ python setup.py install
```
You can **test** `ShareDB` with **pytest** inside the `/tests/` directory
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
Please **discuss** any issues/bugs you're facing, or any changes/features you have in mind by **opening an issue**, following the [Contributor Covenant](https://www.contributor-covenant.org/version/2/0/code_of_conduct). See [COC.md](./docs/COC.md) file for details. Please provide detailed **information**, and code **snippets** to facilitate debugging.

To contribute to `ShareDB`, please **clone** this repository, **commit** your code on a **separate new branch**, and **submit** a **pull request**. Please annotate and describe all **new and modified code** with detailed **comments** and **new unit tests**. Please ensure that modified builds **pass existing unit tests**.  For versioning, we use [SemVer](https://semver.org/).

### Acknowledgements
`ShareDB` is maintained by:

 - Ayaan Hossain | [github.com/ayaanhossain](https://github.com/ayaanhossain) | [@bioalgorithmist](https://twitter.com/bioalgorithmist)

`ShareDB` was originally written to meet data analytics needs in [Prof. Howard Salis](https://twitter.com/hsalis)' Lab at [Penn State University](https://salislab.net/).

Prof. Salis has funded the initial development of `ShareDB`.

### API
`ShareDB` API details can be found in the [API.md](./docs/API.md) file.
