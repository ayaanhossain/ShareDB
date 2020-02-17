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
**\_\_init__(path=None, reset=False, serial='msgpack', compress=False, readers=100, buffer_size=10\*\*5, map_size=10\*\*9)**

ShareDB constructor.

`path` - `string`, a/path/to/a/directory/to/persist/the/data (default=`None`)
`reset` - `boolean`, if `True` - delete and recreate path following parameters (default=`False`)
`serial` - `string`, must be either `'msgpack'` or `'pickle'` (default=`'msgpack'`)
`compress` - `boolean`, if `True` - will compress the values using zlib (default=`False`)
`readers` - `integer`, max no. of processes that'll read data in parallel (default=`40` processes)
`buffer_size` - `integer`, max no. of commits after which a sync is triggered (default=`100,000`)
`map_size` - `integer`, max amount of bytes to allocate for storage (default=`1GB`)

_Returns_ - `ShareDB` object.
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

_Caveats_
