﻿<h1 align="center">
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
>>> myDB.set(key='key', val=['value'])
ShareDB instantiated from ./test.ShareDB/
>>> myDB.set(0, 1).set(1, 2).set(2, 3)
ShareDB instantiated from ./test.ShareDB/
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
ShareDB instantiated from ./test.ShareDB/
```

**get(self, key, default=None)**

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
>>> myDB['some-other-key']
'some-other-value'
>>> myDB['unknown']
Traceback (most recent call last):
...
KeyError: "key=unknown of <class 'str'> is absent"
```

**multiget(self, key_iter, default=None)**

User function to return an generator of values for a given iterable of keys in ShareDB instance.

| argument | type | description | default |
|--|--|--|--|
| `key_iter` | `iterator` | a valid iterable of keys to query ShareDB for values | -- |
| `default` | `object` | a default value to return when key is absent | `None` |

_Returns_ - A `generator` of unpacked `values`, otherwise `default` for absent `keys`.

```python
>>> list(myDB.multiget(key_iter=range(-1, 11)))
[None, 1, 2, 3, 13, 14, 15, 16, 17, 18, 19, None]
```

**has_key(self, key)**

User function to check existence of given key in ShareDB.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a candidate key potentially in ShareDB | -- |

_Alias_ - **\_\_contains__**

_Returns_ - `True` if present, otherwise `False`.

```python
>>> myDB.has_key('key')
True
>>> myDB.has_key('unknown')
False
>>> 'some-other-key' in myDB
True
>>> 100 in myDB
False
```

**length(self)**

User function to return the number of items stored in ShareDB instance.

_Alias_ - **\_\_len__**

_Returns_ - `integer` size of `ShareDB` instance.
```python
>>> myDB.length()
12
>>> len(myDB)
12
```

**remove(self, key)**

User function to remove a key from ShareDB instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a candidate key potentially in ShareDB | -- |

_Returns_ - `self` to `ShareDB` object.

```python
>>> myDB.remove(8).length()
11
```

**\_\_delitem__(self, key)**

Pythonic dunder function to remove a key from ShareDB instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a candidate key potentially in ShareDB | -- |

_Returns_ - `None`.

```python
>>> del myDB[9]
>>> len(myDB)
10
>>> 9 in myDB
False
```

**multiremove(self, key_iter)**

User function to remove all keys specified in an iterator, from ShareDB instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `iterator` | an iterable of keys to be deleted from ShareDB | -- |

_Returns_ - `self` to `ShareDB` object.

```python
>>> myDB.multiremove(range(0, 3)).length()
7
>>> 0 in myDB
False
```

**pop(self, key)**

User function to pop a key from ShareDB instance and return its value.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a valid key to be popped from ShareDB | -- |

_Returns_ - Unpacked `value` corresponding to `key`, otherwise `KeyError`.

```python
>>> myDB.pop(3)
13
>>> myDB.pop(3)
Traceback (most recent call last):
...
KeyError: "key=3 of <class 'int'> is absent"
```

**multipop(self, key_iter)**

User function to return a generator of popped values for a given iterable of keys in ShareDB instance.

| argument | type | description | default |
|--|--|--|--|
| `key_iter` | `iterator` | a valid iterable of keys to be popped from ShareDB | -- |

_Returns_ - A `generator` of unpacked `values`, otherwise `KeyError`.

```python
>>> list(myDB.multipop(range(4, 8)))
[14, 15, 16, 17]
>>> list(myDB.multipop(range(0, 3)))
Traceback (most recent call last):
...
Exception: Given key_iter=range(0, 3) of <class 'range'>, raised: "key=0 of <class 'int'> is absent"
```

**items(self)**

User function to iterate over key-value pairs in ShareDB instance.

_Returns_ - A `generator` of `(key, value)`-pairs in ShareDB.

```python
>>> list(myDB.items())
[('key', ['value']), ('some-other-key', 'some-other-value')]
```

**keys(self)**

User function to iterate over keys in ShareDB instance.

_Alias_ - **\_\_iter__**

_Returns_ - A `generator` of `keys` in ShareDB.

```python
>>> list(myDB.keys())
['key', 'some-other-key']
```

**values(self)**

User function to iterate over values in ShareDB instance.

_Returns_ - A `generator` of `values` in ShareDB.

```python
>>> list(myDB.keys())
[['value'], 'some-other-value']
```
