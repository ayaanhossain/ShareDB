<h1 align="center">
	<a href="https://github.com/ayaanhossain/ShareDB/">
		<img src="../logo/logo.svg"  alt="ShareDB" width="250"/>
    </a>
</h1>

<p align="center">
  <a href="#sharedb-api-documentation">ShareDB API Documentation</a> •
  <a href="../README.md">README</a>
</p>

### `ShareDB` API Documentation
---
**\_\_init__(self, path, reset=False, serial='msgpack', compress=False, readers=100, buffer_size=10\*\*5, map_size=10\*\*9)**

`ShareDB` **constructor**.

| argument | type | description | default |
|--|--|--|--|
| `path` | `string` | a/path/to/a/directory/to/persist/the/data |  -- |
| `reset` | `boolean` | if `True` - delete and recreate path following subsequent parameters | `False` |
| `serial` | `string` | must be either `'msgpack'` or `'pickle'` | `'pickle'` |
| `compress` | `string` | if `True` - will compress the values using `zlib` | `False` |
| `readers` | `integer` | max no. of processes that may read data in parallel | `100` |
| `buffer_size` | `integer` | max no. of commits after which a sync is triggered | `100,000` |
| `map_size` | `integer` | max amount of bytes to allocate for storage, if `None`, then the entire disk is marked for use (safe) | `10**12` (1 TB) |

**_Returns_**: `self` to `ShareDB` object.

```python
>>> from ShareDB import ShareDB
>>> myDB = ShareDB(
	path='./test.ShareDB',
	reset=True,
	readers=10,
	buffer_size=100,
	map_size=10**5)
>>> myDB.ALIVE
True
```
---

**\_\_repr__(self)**

Pythonic dunder function to return a `string` **representation** of `ShareDB` instance.

**_Alias_**: **\_\_str__**

**_Returns_**: A `string` representation of `ShareDB` object.

```python
>>> repr(myDB)
ShareDB instantiated from ./test.ShareDB/
>>> str(myDB)
ShareDB instantiated from ./test.ShareDB/
```
---
**set(self, key, val)**

User function to **insert/overwrite** a **single** `(key, value)` pair in to `ShareDB` instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a valid key to be inserted/updated | -- |
| `val` | `object` | a valid value associated with given key | -- |

**_Returns_**: `self` to `ShareDB` object.

```python
>>> myDB.set(key='key', val=['value'])
ShareDB instantiated from ./test.ShareDB/
>>> myDB.set(0, 1).set(1, 2).set(2, 3)
ShareDB instantiated from ./test.ShareDB/
```
---
**\_\_setitem__(self, key, val)**

Pythonic dunder function to **insert/overwrite** a **single** `(key, value)` pair in to `ShareDB` instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a valid key to be inserted/updated | -- |
| `val` | `object` | a valid value associated with given key | -- |

**_Returns_**: `None`.

```python
>>> myDB['some-other-key'] = 'some-other-value'
```
---
**multiset(self, kv_iter)**

User function to **insert/update multiple** `(key, value)` pairs in to `ShareDB` instance via a single transaction.

| argument | type | description | default |
|--|--|--|--|
| `kv_iter` | `iterable` | an iterable of valid (key, value) pairs | -- |

**_Returns_**: `self` to `ShareDB` object.

```python
>>> myDB.multiset(kv_iter=zip(range(3, 10), range(13, 20)))
ShareDB instantiated from ./test.ShareDB/
```
---
**get(self, key, default=None)**

User function to **query** `value` of a **single** `key` in `ShareDB` instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a valid key to query for associated value | -- |
| `default` | `object` | a default value to return when key is absent | `None` |

**_Returns_**: Unpacked `value` corresponding to `key`, otherwise `default`.

```python
>>> myDB.get(key='key')
['value']
>>> myDB.get(1)
2
>>> myDB.get(key='unknown', default='KEYABSENT')
'KEYABSENT'
```
---
**\_\_getitem__(self, key, val)**

Pythonic dunder function to **query** `value` of a **single** `key` in `ShareDB` instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a valid key to be inserted/updated in ShareDB | -- |

**_Returns_**: Unpacked `value` corresponding to `key`, otherwise `KeyError`.

```python
>>> myDB['some-other-key']
'some-other-value'
>>> myDB['unknown']
Traceback (most recent call last):
...
KeyError: "key=unknown of <class 'str'> is absent"
```
---
**multiget(self, key_iter, default=None)**

User function to **iterate** over `values` of **multiple** `keys` in `ShareDB` instance via a single transaction.

| argument | type | description | default |
|--|--|--|--|
| `key_iter` | `iterable` | an iterable of valid keys to query for values | -- |
| `default` | `object` | a default value to return when a key is absent | `None` |

**_Returns_**: A `generator` of unpacked `values`, otherwise `default` for absent `keys`.

```python
>>> list(myDB.multiget(key_iter=range(-1, 11)))
[None, 1, 2, 3, 13, 14, 15, 16, 17, 18, 19, None]
```
---
**has_key(self, key)**

User function to **check** existence of a **single** `key` in `ShareDB` instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a candidate key to check for presence | -- |

**_Alias_**: **\_\_contains__**

**_Returns_**: `True` if present, otherwise `False`.

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
---
**has_multikey(self, key_iter)**

User function to **check** existence of **multiple** `keys` in `ShareDB` instance via a single transaction.

| argument | type | description | default |
|--|--|--|--|
| `key_iter` | `iterable` | an iterable of candidate keys to check for presence | -- |

**_Returns_**: A `generator` of `booleans`, `True` for present `keys`, otherwise `False`.

```python
>>> list(myDB.has_multikey(range(5)))
[True, True, True, True, True]
>>> list(myDB.has_multikey(range(100, 105)))
[False, False, False, False, False]
```
---
**length(self)**

User function to return the **number of items** stored in `ShareDB` instance.

**_Alias_**: **\_\_len__**

**_Returns_**: `integer` size of `ShareDB` object.

```python
>>> myDB.length()
12
>>> len(myDB)
12
```
---
**remove(self, key)**

User function to **remove** a **single** `key` from `ShareDB` instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a candidate key to remove | -- |

**_Returns_**: `self` to `ShareDB` object.

```python
>>> myDB.remove(8).remove(9).length()
10
```
---
**\_\_delitem__(self, key)**

Pythonic dunder function to **remove** a **single** `key` from `ShareDB` instance.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a candidate key to remove | -- |

**_Returns_**: `None`.

```python
>>> del myDB[7]
>>> len(myDB)
9
>>> 9 in myDB
False
```
---
**multiremove(self, key_iter)**

User function to **remove mutiple** `keys` from `ShareDB` instance via a single transaction.

| argument | type | description | default |
|--|--|--|--|
| `key_iter` | `iterable` | an iterable of candidate keys to remove | -- |

**_Returns_**: `self` to `ShareDB` object.

```python
>>> myDB.multiremove(key_iter=range(0, 3)).length()
6
>>> 0 in myDB
False
```
---
**pop(self, key)**

User function to **pop** a **single** `key` from `ShareDB` instance and return its `value`.

| argument | type | description | default |
|--|--|--|--|
| `key` | `object` | a valid key to be popped | -- |

**_Returns_** - Unpacked `value` corresponding to `key`, otherwise `KeyError`.

```python
>>> myDB.pop(3)
13
>>> myDB.pop(3)
Traceback (most recent call last):
...
KeyError: "key=3 of <class 'int'> is absent"
```
---
**multipop(self, key_iter)**

User function to **pop multiple** `keys` from `ShareDB` instance via a single transaction and iterate over their `values`.

| argument | type | description | default |
|--|--|--|--|
| `key_iter` | `iterable` | an iterable of valid keys to be popped | -- |

**_Returns_**: A `generator` of unpacked `values`, otherwise `KeyError`.

```python
>>> list(myDB.multipop(range(4, 7)))
[14, 15, 16]
>>> list(myDB.multipop(range(0, 3)))
Traceback (most recent call last):
...
Exception: Given key_iter=range(0, 3) of <class 'range'>, raised: "key=0 of <class 'int'> is absent"
```
---
**items(self)**

User function to **iterate** over **all** `(key, value)` pairs in `ShareDB` instance.

**_Returns_**: A `generator` of unpacked `(key, value)` pairs.

```python
>>> list(myDB.items())
[('key', ['value']), ('some-other-key', 'some-other-value')]
```
---
**keys(self)**

User function to **iterate** over **all** `keys` in `ShareDB` instance.

**_Alias_**: **\_\_iter__**

**_Returns_**: A `generator` of unpacked `keys`.

```python
>>> list(myDB.keys())
['key', 'some-other-key']
```
---

**values(self)**

User function to **iterate** over **all** `values` in `ShareDB` instance.

**_Returns_**: A `generator` of unpacked `values`.

```python
>>> list(myDB.values())
[['value'], 'some-other-value']
```
---
**popitem(self)**

User function to **pop** a **single** `(key, value)` pair in `ShareDB` instance.

**_Returns_**: A popped unpacked `(key, value)` pair.

```python
>>> myDB.popitem()
('key', ['value'])
>>> myDB.popitem()
('some-other-key', 'some-other-value')
>>> len(myDB)
0
```
---
**multipopitem(self, num_items=1)**

User function to **iterate** over **multiple popped** `(key, value)` pairs from `ShareDB` instance via a single transaction.

| argument | type | description | default |
|--|--|--|--|
| `num_items` | `integer` | max no. of items to pop | `1` |

**_Returns_**: A generator of up to `num_items` popped unpacked `(key, value)` pairs.

```python
>>> myDB.multiset(kv_iter=zip(range(5), range(5, 10))).length()
5
>>> list(myDB.multipopitem(num_items=10))
[(0, 5), (1, 6), (2, 7), (3, 8), (4, 9)]
>>> len(myDB)
0
```
---
**sync(self)**

User function to **flush all commits** to `ShareDB` instance on disk.

**_Returns_**: `self` to `ShareDB` object.

```python
>>> myDB.multiset(kv_iter=zip(range(5), range(5, 10))).sync()
ShareDB instantiated from ./test.ShareDB/
```
---
**clear(self)**

User function to **remove all data** stored in `ShareDB` instance.

**_Returns_**: `self` to `ShareDB` object.

```python
>>> myDB.clear()
ShareDB instantiated from ./test.ShareDB/
>>> 3 in myDB
False
>>> len(myDB)
0
```
---
**close(self)**

User function to **save and close** `ShareDB` instance.

**_Returns_**: `True` if closed, otherwise `False`.

```python
>>> myDB.ALIVE
True
>>> myDB.close()
True
>>> myDB.close()
False
>>> myDB.ALIVE
False
>>> myDB.set(key='key', val=['value'])
RuntimeError: Access to ShareDB instantiated from ./test.ShareDB/ has been closed or dropped
```

**drop(self)**

User function to **delete** `ShareDB` instance.

**_Returns_**: `True` if dropped, otherwise `False`.

```python
>>> myDB = ShareDB(path=myDB.PATH)
>>> myDB.ALIVE
True
>>> myDB.drop()
True
>>> myDB.ALIVE
False
>>> myDB.set(key='key', val=['value'])
RuntimeError: Access to ShareDB instantiated from ./test.ShareDB/ has been closed or dropped
```
---
