<h1 align="center">
	<a href="https://github.com/ayaanhossain/ShareDB/">
		<img src="../logo/logo.svg"  alt="ShareDB" width="250"/>
    </a>
</h1>

<p align="center">
  <a href="#api-documentation">API Documentation</a> •
  <a href="../README.md">README</a>
</p>

### API Documentation
**\_\_init__(self, path=None, reset=False, serial='msgpack', compress=False, readers=100, buffer_size=10\*\*5, map_size=10\*\*9)**

ShareDB constructor.
| argument | type | description | default |
|--|--|--|--|
| `path` | `string` | a/path/to/a/directory/to/persist/the/data |  `None`|
| `reset` | `boolean` | if `True` - delete and recreate path following subsequent parameters | `False` |
| `serial` | `string` | must be either `'msgpack'` or `'pickle'` | `False`
| `compress` | `string` | if `True` - will compress the values using `zlib` | `False`
| `readers` | `integer` | max no. of processes that may read data in parallel | `100`
| `buffer_size` | `integer` | max no. of commits after which a sync is triggered | `100,000`
| `map_size` | `integer` | max amount of bytes to allocate for storage | `1GB`

_Returns_ - `self` to `ShareDB` object.
```python
>>> myDB = ShareDB(
	path='./test.ShareDB',
	reset=True,
	readers=10,
	buffer_size=100,
	map_size=10**5)
>>> myDB.ALIVE
True
```

**\_\_repr__(self)**

Pythonic dunder function to return a string representation of ShareDB instance.

_Alias_ - **\_\_str__**

_Returns_ - A `string` representation of ShareDB object.

```python
>>> myDB = ShareDB(path='./test.ShareDB', reset=True)
>>> myDB
ShareDB instantiated from ./test.ShareDB/
```

**set(self, key, val)**

User function to insert/overwrite a key-value pair into ShareDB instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a valid key to be inserted/updated in ShareDB |  `None`|
| `val` | `object` | a valid value/object associated with given key | `None` |

_Alias_ - **\_\_setitem__**

_Returns_ - `self` to `ShareDB` object.

```python
>>> myDB.set(key='key', value=['value'])
>>> myDB['some-other-key'] = 'some-other-value'
>>> myDB.set(0, 1).set(1, 2).set(2, 3)
```
