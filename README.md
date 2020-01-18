![ShareDB](./logo.png)
---
ShareDB is a lightweight on-disk key-value store with a dictionary-like interface built on top of LMDB and is intended to replace a built-in python dictionary when

 1. the data to store needs to persist on disk for later reuse,
 2. the data needs to be read across multiple processes with minimal overhead, and 
 3. the keys and values can be (de)serialized via msgpack or cPickle.

ShareDB operates via an LMDB structure in an optimistic manner for reading and writing data. As long as you maintain a one-writer-many-reader workflow everything should be fine. Sending a ShareDB instance from parent to children processes is fine, or you may open the same ShareDB in children processes for reading. Parallel writes made in children processes are not safe; they are not guaranteed to be written, and may corrupt instance.

A sample use case

### Table of Contents
 * [ShareDB in Action](#sharedb-in-action)
 * [Requirements](#requirements)
 * [Installation](#installation)
 * [License and Contribution](#license-and-contribution)
 * [API Reference](#api-reference)

### ShareDB in Action

    >>> from ShareDB import ShareDB           # Easy import
    >>> print(ShareDB.__version__)            # Check version
    0.1.6
    >>> myDB = ShareDB(path='./test.ShareDB') # Store ShareDB locally
    >>> myDB['Name'] = ['Ayaan Hossain']      # Insert information
    >>> myDB.get(key='Name')                  # Retrieve values
    ['Ayaan Hossain']
    >>> # Insert/update multiple items while being pythonic!
    >>> len(myDB.multiset(kv_iter=zip(range(0, 10), range(10, 20))).sync())
    11
    >>> 7 in myDB                             # Membership queries work
    True
    >>> myDB['non-existent key']              # KeyError on invalid get as expected
    Traceback (most recent call last):
    ...
    KeyError: "key=non-existent key of <type 'str'> is absent"
    >>> myDB.pop(7)                           # Pop a key just like a dictionary!
	17
	>>> list(myDB.multipopitem(num_items=5))  # Or, pop as many items as you need
    [(0, 10), (1, 11), (2, 12), (3, 13), (4, 14)]
    >>> myDB.clear().length()                 # Remove everything if you must
    0
    >>> myDB.drop()                           # Close/delete when you're done!
    True

### Requirements

### Installation

### License and Contribution

### API Reference

