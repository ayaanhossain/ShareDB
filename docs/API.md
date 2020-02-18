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
| `path` | `string` | a/path/to/a/directory/to/persist/the/data |  -- |
| `reset` | `boolean` | if `True` - delete and recreate path following subsequent parameters | `False` |
| `serial` | `string` | must be either `'msgpack'` or `'pickle'` | `False` |
| `compress` | `string` | if `True` - will compress the values using `zlib` | `False` |
| `readers` | `integer` | max no. of processes that may read data in parallel | `100` |
| `buffer_size` | `integer` | max no. of commits after which a sync is triggered | `100,000` |
| `map_size` | `integer` | max amount of bytes to allocate for storage | `1GB` |

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

_Returns_ - A `string` representation of `ShareDB` object.

```python
>>> myDB
ShareDB instantiated from ./test.ShareDB/
```

**set(self, key, val)**

User function to insert/overwrite a key-value pair into ShareDB instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a valid key to be inserted/updated in ShareDB | -- |
| `val` | `object` | a valid value/object associated with given key | -- |

_Returns_ - `self` to `ShareDB` object.

```python
>>> myDB.set(key='key', value=['value'])
>>> myDB.set(0, 1).set(1, 2).set(2, 3)
```

**\_\_setitem__(self, key, val)**

Pythonic dunder function to insert/overwrite a key-value pair into ShareDB instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a valid key to be inserted/updated in ShareDB | -- |
| `val` | `object` | a valid value/object associated with given key | -- |

_Returns_ - `None`

```python
>>> myDB['some-other-key'] = 'some-other-value'
```

**multiset(self, kv_iter)**

User function to insert/update multiple key-value pairs into ShareDB instance.

| argument | type | description | default |
|--|--|--|--|
| `kv_iter` | `iterator` | a valid key-value iterator to populate ShareDB via a single transaction | -- |

_Returns_ - `self` to `ShareDB` object.

```python
>>> myDB.multiset(kv_iter=zip(range(3, 10), range(13, 20)))
```

**get(self, key)**

User function to query value for a given key in ShareDB instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a valid key to query ShareDB for associated value | -- |
| `default` | `object` | a default value to return when key is absent | -- |

_Returns_ - Unpacked `value` corresponding to `key`, otherwise `default`.

```python
>>> myDB.get(key='key')
['value']
>>> myDB.get(1)
2
>>> myDB.get(key='unknown', default='KEYABSENT')
'KEYABSENT'
```

**\_\_getitem__(self, key, val)**

Pythonic dunder function to query value for a given key in ShareDB instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a valid key to be inserted/updated in ShareDB | -- |

_Returns_ - Unpacked `value` corresponding to `key`, otherwise `KeyError`.

```python
>>> myDB['some-other-key'] = 'some-other-value'
>>> myDB['unknown']
Traceback (most recent call last):
...
KeyError: "key=unknown of <class 'str'> is absent"
```

**multiget(self, key_iter)**

User function to return an iterator of values for a given iterable of keys in ShareDB instance.

| argument | type | description | default |
|--|--|--|--|
| `key_iter` | `iterator` | a valid iterable of keys to query ShareDB for values | -- |
| `default` | `object` | a default value to return when key is absent | `None` |

_Returns_ - A `generator` of unpacked `values`, otherwise `default` for absent `keys`.

```python
>>> list(myDB.multiget(key_iter=range(11)))
[1, 2, 3, 13, 14, 15, 16, 17, 18, 19, None]
```
