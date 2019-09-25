'''
MIT License

Copyright (c) 2019 Ayaan Hossain

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

# Maybe Core
import random

# Not core
import time   # Not core
import sys    # Not core
import multiprocessing

import collections

# Core imports
import shutil
import os
import uuid
import msgpack
import cPickle
import lmdb

class ShareDB(object):
    '''
    ShareDB is a lightweight on-disk key-value store with a  dictionary-like interface
    built on top of LMDB and is intended to replace a python dictionary when:

    (1) the amount of data to store will not fit in main memory,
    (2) the data needs to persist on disk for later reuse,
    (3) the data needs to be read across multiple processes,
    (4) keys and values are msgpack/pickle compliant, and
    (5) all key-value operations must be fast with minimal overhead.

    Note: cPickle functionality in progress.

    ShareDB operates via an LMDB structure in an optimistic manner for reading and 
    writing data. As long as you maintain a one-writer-many-reader workflow there
    should not be any problem. Sending a ShareDB instance from parent to children 
    processes is fine, or you may open several instances in children processes 
    for reading. Parallel writes made in children processes are not guaranteed to 
    be reflected back in the original ShareDB instance, and may corrupt instance.
    '''

    def __init__(self,
        path=None,
        reset=False,
        readers=100,
        buffer_size=10**5,
        map_size=1000 * 1000 * 1000 * 1000):
        '''
        ShareDB constructor.

        :: path        - a/path/to/a/directory/to/presist/the/data (default=None)
        :: reset       - boolean, if True - delete and recreate path (default=False)
        :: readers     - max no. of processes that'll read data in parallel (default=40 processes)
        :: buffer_size - max no. of commits after which a sync is triggered (default=100,000)
        :: map_size    - max amount of bytes to allocate for storage (default=1TB)

        __init__ test cases.

        >>> myDB = ShareDB()
        Traceback (most recent call last):
        Exception: Given path=None of <type 'NoneType'>, raised: 'NoneType' object has no attribute 'endswith'
        >>> myDB = ShareDB(path=True)
        Traceback (most recent call last):
        Exception: Given path=True of <type 'bool'>, raised: 'bool' object has no attribute 'endswith'
        >>> myDB = ShareDB(path=123)
        Traceback (most recent call last):
        Exception: Given path=123 of <type 'int'>, raised: 'int' object has no attribute 'endswith'
        >>> myDB = ShareDB(path='/22.f')
        Traceback (most recent call last):
        Exception: Given path=/22.f.ShareDB/ of <type 'str'>, raised: [Errno 13] Permission denied: '/22.f.ShareDB/'
        >>> myDB = ShareDB(path='./test_init.ShareDB', reset=True)
        >>> myDB.ALIVE
        True
        >>> len(myDB) == 0
        True
        >>> myDB.PATH
        './test_init.ShareDB/'
        >>> myDB.PARALLEL
        100
        >>> shutil.rmtree(myDB.PATH)
        '''
        # Check if a path is valid for creating ShareDB
        try:
            path  = self._trim_suffix(given_str=path, suffix='/')
            path  = self._trim_suffix(given_str=path, suffix='.ShareDB')
            path += '.ShareDB/'
            if not os.path.isdir(path):
                os.makedirs(path)
            else:
                checkfile = 'checkfile{}$'.format(uuid.UUID(bytes=os.urandom(16), version=4))
                checkpath = path + checkfile
                with open(checkpath, 'w') as tempfile:
                    pass
                os.remove(checkpath)
        except Exception as E:
            raise Exception('Given path={} of {}, raised: {}'.format(path, type(path), E))

        # Clear path if necessary
        if reset:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            elif os.path.exists(path):
                os.remove(path)

        # Setup/Load ShareDB
        self.ALIVE    = True           # Instance is alive
        self.PATH     = path           # Path to store/load the DB
        self.BCSIZE   = buffer_size    # Trigger sync after this many items inserted
        self.BQSIZE   = 0              # Approx. no. of items to sync in ShareDB
        self.MSLIMIT  = map_size       # Memory map size, maybe larger than RAM
        self.PARALLEL = readers        # Number of processes reading in parallel
        self.DB = lmdb.open(self.PATH, # Configure ShareDB
            subdir=True,
            map_size=self.MSLIMIT,
            create=True,
            readahead=False,
            writemap=True,
            map_async=True,
            max_readers=self.PARALLEL,
            max_dbs=0,
            lock=True
        )

    def _trim_suffix(self, given_str, suffix):
        '''
        Internal helper function to trim suffixes in given_str.
        '''
        if given_str.endswith(suffix):
            return given_str[:-len(suffix)]
        return given_str

    def __repr__(self):
        '''
        Pythonic dunder function to return a string representation of ShareDB instance.
        
        __repr__ test cases.

        >>> myDB = ShareDB(path='./test_repr.ShareDB', reset=True)
        >>> myDB
        ShareDB instantiated from ./test_repr.ShareDB/.
        >>> myDB.close()
        >>> shutil.rmtree(myDB.PATH)
        '''
        return 'ShareDB instantiated from {}.'.format(self.PATH)

    def __str__(self):
        '''
        Pythonic dunder function to return a string representation of ShareDB instance.

        __str__ test cases.

        >>> myDB = ShareDB(path='./test_str.ShareDB', reset=True)
        >>> myDB
        ShareDB instantiated from ./test_str.ShareDB/.
        >>> myDB.close()
        >>> shutil.rmtree(myDB.PATH)
        '''
        return repr(self)

    def _get_packed_key(self, key):
        '''
        Internal helper function to try and msgpack given key.

        :: key - a valid key to be inserted/updated in ShareDB

        _get_packed_key test cases.

        >>> myDB = ShareDB(path='./test_get_packed_key.ShareDB', reset=True)
        >>> test_key = [1, '2', 3.0, None]
        >>> myDB._get_packed_key(key=test_key) == msgpack.packb(test_key)
        True
        >>> myDB._get_packed_key(key=set(test_key[:1]))
        Traceback (most recent call last):
        Exception: Given key=set([1]) of <type 'set'>, raised: can't serialize set([1])
        >>> myDB._get_packed_key(key=None)
        Traceback (most recent call last):
        Exception: ShareDB cannot use <type 'NoneType'> objects as keys or values
        >>> shutil.rmtree(myDB.PATH)
        '''
        if key is None:
            raise Exception('ShareDB cannot use {} objects as keys or values'.format(type(None)))
        try:
            key = msgpack.packb(key)
        except Exception as E:
            raise Exception('Given key={} of {}, raised: {}'.format(key, type(key), E))
        return key

    def _get_unpacked_key(self, key):
        '''
        Internal helper function to try and un-msgpack given key.

        :: key - a valid key to be inserted/updated in ShareDB

        _get_packed_key test cases.

        >>> myDB = ShareDB(path='./test_get_unpacked_key.ShareDB', reset=True)
        >>> test_key = [1, '2', 3.0, None]
        >>> myDB._get_unpacked_key(key=myDB._get_packed_key(key=test_key)) == test_key
        True
        >>> shutil.rmtree(myDB.PATH)
        '''
        if key is None:
            raise Exception('ShareDB cannot use {} objects as keys or values'.format(type(None)))
        try:
            key = msgpack.unpackb(key)
        except Exception as E:
            raise Exception('Given key={} of {}, raised: {}'.format(key, type(key), E))
        return key

    def _get_packed_val(self, val):
        '''
        Internal helper function to try and msgpack given value.

        :: val - a valid value/object associated with given key

        _get_packed_val test cases.

        >>> myDB = ShareDB(path='./test_get_packed_val.ShareDB', reset=True)
        >>> test_val = {0: [1, '2', 3.0, None]}
        >>> myDB._get_packed_val(val=test_val) == msgpack.packb(test_val)
        True
        >>> myDB._get_packed_val(val=set(test_val[0][:1]))
        Traceback (most recent call last):
        Exception: Given value=set([1]) of <type 'set'>, raised: can't serialize set([1])
        >>> myDB._get_packed_val(val=None)
        Traceback (most recent call last):
        Exception: ShareDB cannot use <type 'NoneType'> objects as keys or values
        >>> shutil.rmtree(myDB.PATH)
        '''
        if val is None:
            raise Exception('ShareDB cannot use {} objects as keys or values'.format(type(None)))
        try:
            val = msgpack.packb(val)
        except Exception as E:
            raise Exception('Given value={} of {}, raised: {}'.format(val, type(val), E))
        return val

    def _get_unpacked_val(self, val):
        '''
        Internal helper function to try and un-msgpack given value.

        :: val - a valid value/object associated with given key

        _get_packed_val test cases.

        >>> myDB = ShareDB(path='./test_get_unpacked_val.ShareDB', reset=True)
        >>> test_val = {0: [1, '2', 3.0, None]}
        >>> myDB._get_unpacked_val(val=myDB._get_packed_val(val=test_val)) == test_val
        True
        >>> shutil.rmtree(myDB.PATH)
        '''
        if val is None:
            raise Exception('ShareDB cannot use {} objects as keys or values'.format(type(None)))
        try:
            val = msgpack.unpackb(val)
        except Exception as E:
            raise Exception('Given value={} of {}, raised: {}'.format(val, type(val), E))
        return val

    def _trigger_sync(self):
        '''
        Internal helper function to trigger sync once enough items set.
        '''
        if self.BQSIZE >= self.BCSIZE:
            self.sync()
            self.BQSIZE = 0
        return None

    def _insert_kv_in_txn(self, key, val, txn):
        '''
        Internal helper function to insert key-value pair via txn and trigger sync.

        :: key - a valid key to be inserted/updated in ShareDB
        :: val - a valid value/object associated with given key
        :: txn - a transaction interface for insertion
        '''
        key = self._get_packed_key(key=key)
        val = self._get_packed_val(val=val)
        txn.put(key=key, value=val)
        self.BQSIZE += 1
        self._trigger_sync()
        return None

    def multiset(self, kv_iter):
        '''
        User function to insert/update multiple key-value pairs into ShareDB instance.

        :: kv_iter - a valid key-value iterator to populate ShareDB

        multiset test cases.

        >>> myDB = ShareDB(path='./test_multi_set.ShareDB', reset=True)
        >>> kv_generator = ((tuple(range(i, i+5)), range(i+5, i+10)) for i in range(10))
        >>> myDB.multiset(kv_iter=kv_generator).sync().length()
        10
        >>> myDB = ShareDB(path='./test_multi_set.ShareDB', reset=False)
        >>> len(myDB)
        10
        >>> kv_generator = ((tuple(range(i, i+5)), range(i+5, i+10)) for i in range(3000, 3005))
        >>> myDB.multiset(kv_iter=kv_generator)
        ShareDB instantiated from ./test_multi_set.ShareDB/.
        >>> len(myDB)
        15
        >>> for i in range(3005, 3010): myDB[tuple(range(i, i+5))] = range(i+5, i+10)
        >>> len(myDB)
        20
        >>> myDB.close()
        >>> myDB = ShareDB(path='./test_multi_set.ShareDB', reset=False)
        >>> len(myDB)
        20
        >>> myDB[tuple(range(3005, 3010))] == range(3010, 3015)
        True
        >>> myDB[tuple(range(1))] = set(range(1))
        Traceback (most recent call last):
        Exception: Given value=set([0]) of <type 'set'>, raised: can't serialize set([0])
        >>> myDB[set(range(1))] = range(1)
        Traceback (most recent call last):
        Exception: Given key=set([0]) of <type 'set'>, raised: can't serialize set([0])
        >>> shutil.rmtree(myDB.PATH)
        '''
        with self.DB.begin(write=True) as kvsetter:
            try:
                for key,val in kv_iter:
                    self._insert_kv_in_txn(key=key, val=val, txn=kvsetter)
            except Exception as E:
                raise Exception('Given kv_iter={} of {}, raised: {}'.format(kv_iter, type(kv_iter), E))
        return self

    def set(self, key, val):
        '''
        User function to insert/overwrite a key-value pair into ShareDB instance.

        :: key - a valid key to be inserted/updated in ShareDB
        :: val - a valid value/object associated with given key

        set test cases.

        >>> myDB = ShareDB(path='./test_set.ShareDB', reset=True)
        >>> myDB.set(key=('NAME'), val='Ayaan Hossain')
        ShareDB instantiated from ./test_set.ShareDB/.
        >>> myDB.set(key=['KEY'], val=set(['SOME_VALUE']))
        Traceback (most recent call last):
        Exception: Given value=set(['SOME_VALUE']) of <type 'set'>, raised: can't serialize set(['SOME_VALUE'])
        >>> myDB.set(key=(1, 2, 3, 4), val='SOME_VALUE')
        ShareDB instantiated from ./test_set.ShareDB/.
        >>> myDB.set(key='ANOTHER KEY', val=[1, 2, 3, 4])
        ShareDB instantiated from ./test_set.ShareDB/.
        >>> shutil.rmtree(myDB.PATH)
        '''
        with self.DB.begin(write=True) as kvsetter:
            self._insert_kv_in_txn(key=key, val=val, txn=kvsetter)
        return self

    def __setitem__(self, key, val):
        '''
        Pythonic dunder function to insert/overwrite a key-value pair into ShareDB instance.

        :: key - a valid key to be inserted/updated in ShareDB
        :: val - a valid value/object associated with given key

        __setitem__ test cases.

        >>> myDB = ShareDB(path='./test_set_dunder.ShareDB', reset=True)
        >>> myDB['NAME']  = 'Ayaan Hossain'
        >>> myDB[['KEY']] = 'SOME_VALUE'
        >>> myDB['KEY'] = 'SOME_VALUE'
        >>> myDB['ANOTHER KEY'] = [1, 2, 3, 4]
        >>> myDB[['KEY']] == 'SOME_VALUE'
        True
        >>> myDB[set(['KEY'])] = 'SOME_VALUE'
        Traceback (most recent call last):
        Exception: Given key=set(['KEY']) of <type 'set'>, raised: can't serialize set(['KEY'])
        >>> shutil.rmtree(myDB.PATH)
        '''
        return self.set(key=key, val=val)

    def length(self):
        '''
        User function to return the number of items stored in ShareDB.

        length test cases.

        >>> myDB = ShareDB(path='./test_length', reset=True)
        >>> for i in range(500, 600): myDB[i] = 2.0*i
        >>> len(myDB)
        100
        >>> myDB.sync().clear().length()
        0
        >>> shutil.rmtree(myDB.PATH)
        '''
        return int(self.DB.stat()['entries']) 

    def __len__(self):
        '''
        Pythonic dunder function to return the number of items stored in ShareDB.

        __len__ test cases.

        >>> myDB = ShareDB(path='./test_len.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = i**2
        >>> len(myDB)
        100
        >>> myDB.close()
        >>> myDB = ShareDB(path='./test_len.ShareDB', reset=False)
        >>> len(myDB)
        100
        >>> myDB.clear()
        ShareDB instantiated from ./test_len.ShareDB/.
        >>> len(myDB)
        0
        >>> shutil.rmtree(myDB.PATH)
        '''
        return self.length()

    def _get_val_on_disk(self, key, txn, packed=False, default=None):
        '''
        Internal helper function to return the packed value associated with given key.

        :: key     - a valid key to query ShareDB for associated value
        :: txn     - a transaction interface for query
        :: packed  - boolean, If True - will attempt packing key (default=False)
        :: default - a default value to return when key is absent (default=None)
        '''
        if not packed:
            key = self._get_packed_key(key=key)
        return txn.get(key=key, default=default)

    def _get_unpacked_val_on_disk(self, key, txn, packed=False, default=None):
        '''
        Internal helper function to return the unpacked value associated with given key.
        
        :: key     - a valid key to query ShareDB for associated value
        :: txn     - a transaction interface for query
        :: packed  - boolean, If True - will attempt packing key (default=False)
        :: default - a default value to return when key is absent (default=None)
        '''
        val = self._get_val_on_disk(key=key, txn=txn, packed=packed, default=default)
        if val is default:
            return default
        return self._get_unpacked_val(val)

    def get(self, key, default=None):
        '''
        User function to query value for a given key else return default.

        :: key     - a valid key to query ShareDB for associated value
        :: default - a default value to return when key is absent (default=None)

        get test cases.
        
        >>> myDB = ShareDB(path='./test_get.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = i**0.5
        >>> len(myDB)
        100
        >>> myDB = ShareDB(path='./test_get.ShareDB', reset=False)
        >>> for i in range(100): assert myDB.get(i) == i**0.5
        >>> myDB.get(key=81)
        9.0
        >>> myDB.get(key=202, default='SENTIENTDEFAULT')
        'SENTIENTDEFAULT'
        >>> myDB.clear()
        ShareDB instantiated from ./test_get.ShareDB/.
        >>> myDB.get(key=81, default='SENTIENTDEFAULT')
        'SENTIENTDEFAULT'
        >>> shutil.rmtree(myDB.PATH)
        '''
        with self.DB.begin(write=False) as kvgetter:
            val = self._get_unpacked_val_on_disk(key=key, txn=kvgetter, packed=False, default=default)
        return val

    def __getitem__(self, key):
        '''
        Pythonic dunder function to query value for a given key.

        :: key - a valid key to query ShareDB for associated value

        __getitem__ test cases.

        >>> myDB = ShareDB(path='./test_getitem.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = i**0.5
        >>> len(myDB)
        100
        >>> myDB.close()
        >>> myDB = ShareDB(path='./test_getitem.ShareDB', reset=False)
        >>> myDB[49]
        7.0
        >>> myDB[49.0]
        >>> myDB[set([49.0])]
        Traceback (most recent call last):
        Exception: Given key=set([49.0]) of <type 'set'>, raised: can't serialize set([49.0])
        >>> shutil.rmtree(myDB.PATH)
        '''
        return self.get(key=key, default=None)

    def multiget(self, key_iter, default=None):
        '''
        User function to return an iterator of values for a given iterable of keys.

        :: key_iter - a valid iterable of keys to query ShareDB for values
        :: default  - a default value to return when key is absent in ShareDB (default=None)

        multiget test cases.

        >>> myDB = ShareDB(path='./multiget.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = i**2
        >>> len(myDB)
        100
        >>> myDB.close()
        >>> myDB = ShareDB(path='./multiget.ShareDB', reset=False)
        >>> len(list(myDB.multiget(key_iter=range(100), default=None))) == 100
        True
        >>> myDB.multiget(key_iter=range(100, 110), default=False).next()
        False
        >>> shutil.rmtree(myDB.PATH)
        '''
        with self.DB.begin(write=False) as kvgetter:
            try:
                for key in key_iter:
                    yield self._get_unpacked_val_on_disk(key=key, txn=kvgetter, packed=False, default=default)
            except Exception as E:
                raise Exception('Given key_iter={} of {}, raised: {}'.format(key_iter, type(key_iter), E))

    def has_key(self, key):
        '''
        User function to check existence of given key in ShareDB.

        :: key - a candidate key potentially in ShareDB

        has_key test cases.

        >>> myDB = ShareDB(path='./test_has_key', reset=True)
        >>> myDB.multiset((i, [i**0.5, i**2.0]) for i in range(100, 200))
        ShareDB instantiated from ./test_has_key.ShareDB/.
        >>> len(myDB)
        100
        >>> myDB.has_key(150)
        True
        >>> myDB.clear().has_key(150)
        False
        >>> myDB.multiset(((i,[i**0.5, i**2.0]) for i in range(100))).has_key(49)
        True
        >>> shutil.rmtree(myDB.PATH)
        '''
        with self.DB.begin(write=False) as kvgetter:
            val = self._get_val_on_disk(key=key, txn=kvgetter, packed=False, default=None)
        if val is None:
            return False
        return True
    
    def __contains__(self, key):
        '''
        Pythonic dunder function to check existence of given key in ShareDB.

        :: key - a candidate key potentially in ShareDB

        ___contain___ test cases.

        >>> myDB = ShareDB(path='./test_contains', reset=True)
        >>> for i in range(100): myDB[i] = [i**0.5, i**2]
        >>> 95 in myDB
        True
        >>> 1 in myDB
        True
        >>> 16**6 in myDB
        False
        >>> myDB.close()
        >>> myDB = ShareDB(path='./test_contains.ShareDB', reset=False)
        >>> 1 in myDB
        True
        >>> 95 in myDB
        True
        >>> 102 in myDB
        False
        >>> myDB.clear().length()
        0
        >>> 64 in myDB.multiset(((i,[i**0.5, i**2.0]) for i in range(100)))
        True
        >>> shutil.rmtree(myDB.PATH)
        '''        
        return self.has_key(key=key)

    # This block onwards need refactoring, tests and comments

    def _del_pop_from_disk(self, key, txn, opr, packed=False):
        '''
        Internal helper function to delete/pop key-value pair via txn and trigger sync.

        :: key    - a candidate key potentially in ShareDB
        :: txn    - a transaction interface for delete/pop
        :: opr    - string, must be 'del' or 'pop' specifying the operation
        :: packed - boolean, If True - will attempt packing key (default=False)
        '''
        if not packed:
            key = self._get_packed_key(key=key)
        if opr == 'pop':
            val = self._get_unpacked_val(val=txn.pop(key=key))
        elif opr == 'del':
            txn.delete(key=key)
            val = None
        else:
            raise Exception('opr must be \'del\' or \'pop\' not {}'.format(opr))
        self.BQSIZE += 1
        self._trigger_sync()        
        return val

    def multiremove(self, key_iter):
        '''
        User function to remove all key-value pairs specified in the iterable of keys.

        :: key_iter - a valid iterable of keys to be deleted from ShareDB
        
        multiremove test cases.

        >>> myDB = ShareDB(path='./test_multiremove.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = i**2
        >>> len(myDB)
        100
        >>> myDB.close()
        >>> myDB = ShareDB(path='./test_multiremove.ShareDB', reset=False)
        >>> myDB.multiremove(range(100)).length()
        0
        >>> 0 in myDB
        False
        >>> shutil.rmtree(myDB.PATH)
        '''
        with self.DB.begin(write=True) as keydeler:
            try:
                for key in key_iter:
                    self._del_pop_from_disk(key=key, txn=keydeler, opr='del', packed=False)
            except Exception as E:
                raise Exception('Given key_iter={} of {}, raised: {}'.format(key_iter, type(key_iter), E))
        return self

    def remove(self, key):
        '''
        User function to remove a key-value pair.

        :: key - a valid key to be deleted from ShareDB
        
        remove test cases.

        >>> myDB = ShareDB(path='./test_remove.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = i**0.5
        >>> len(myDB)
        100
        >>> myDB.close()
        >>> myDB = ShareDB(path='./test_remove', reset=False)
        >>> myDB.remove(99).length()
        99
        >>> 99 in myDB
        False
        >>> shutil.rmtree(myDB.PATH)
        '''
        with self.DB.begin(write=True) as keydeler:
            self._del_pop_from_disk(key=key, txn=keydeler, opr='del', packed=False)
        return self

    def __delitem__(self, key):
        '''
        Pythonic dunder function to remove a key-value pair.

        :: key - a valid key to be deleted from ShareDB
        
        __delitem__ test cases.

        >>> myDB = ShareDB(path='./test_delitem.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = i**0.5
        >>> len(myDB)
        100
        >>> myDB.close()
        >>> myDB = ShareDB(path='./test_delitem', reset=False)
        >>> del myDB[99]
        >>> 99 in myDB
        False
        >>> shutil.rmtree(myDB.PATH)
        '''
        return self.remove(key=key)

    def multipop(self, key_iter, default=None):
        '''
        User function to return an iterator of popped values for a given iterable of keys.

        :: key_iter - a valid iterable of keys to be deleted from ShareDB
        
        multipop test cases.

        >>> myDB = ShareDB(path='./test_multipop.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = [i**0.5]
        >>> len(myDB)
        100
        >>> myDB.close()
        >>> myDB = ShareDB(path='./test_multipop', reset=False)
        >>> pop_iter = myDB.multipop(range(49, 74))
        >>> pop_iter.next()
        [7.0]
        >>> len(list(pop_iter))
        24
        >>> len(myDB)
        75
        >>> shutil.rmtree(myDB.PATH)
        '''
        with self.DB.begin(write=True) as keypopper:
            try:
                for key in key_iter:
                    yield self._del_pop_from_disk(key=key, txn=keypopper, opr='pop', packed=False)
            except Exception as E:
                raise Exception('Given key_iter={} of {}, raised: {}'.format(key_iter, type(key_iter), E))

    def pop(self, key, default=None):
        '''
        User function to pop a key and return its value.

        :: key - a valid key to be deleted from ShareDB
        
        pop test cases.

        >>> myDB = ShareDB(path='./test_pop.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = [i**0.5]
        >>> len(myDB)
        100
        >>> myDB.close()
        >>> myDB = ShareDB(path='./test_pop', reset=False)
        >>> myDB.pop(49)
        [7.0]
        >>> 49 in myDB
        False
        >>> len(myDB)
        99
        >>> shutil.rmtree(myDB.PATH)
        '''
        with self.DB.begin(write=True) as keypopper:
            val = self._del_pop_from_disk(key=key, txn=keypopper, opr='pop', packed=False)
        return val

    def multipopitem(self):
        # TODO
        pass

    def popitem(self):
        # TODO
        pass

    def _iter_on_disk_kv(self, yield_key=False, unpack_key=False, yield_val=False, unpack_val=False):
        with self.DB.begin(write=False) as kviter:
            with kviter.cursor() as kvcursor:
                for key,val in kvcursor:
                    if unpack_key:
                        key = self._get_unpacked_key(key=key)
                    if unpack_val:
                        val = self._get_unpacked_val(val=val)
                    if yield_key and not yield_val:
                        yield key
                    elif yield_val and not yield_key:
                        yield val
                    elif yield_key and yield_val:
                        yield key,val
                    else:
                        raise Exception('All four params to _iter_on_disk_kv cannot be False or None')

    def items(self):
        return self._iter_on_disk_kv(yield_key=True, unpack_key=True, yield_val=True, unpack_val=True)

    def keys(self):
        return self._iter_on_disk_kv(yield_key=True, unpack_key=True, yield_val=False, unpack_val=False)

    def values(self):
        return self._iter_on_disk_kv(yield_key=False, unpack_key=False, yield_val=True, unpack_val=True)

    def popitem(self, key, default=None, sync=True):
        # TODO
        pass    

    def update():
        # TODO
        pass

    def sync(self):
        '''
        User function to flush ShareDB inserts/changes/commits on to disk.
        '''
        self.DB.sync()
        return self

    def compact(self):
        # TODO
        pass    

    def clear(self):
        '''
        User function to remove all data stored in a ShareDB instance.

        clear test cases.

        >>> myDB = ShareDB(path='./test_clear/', reset=True)
        >>> for i in range(100): myDB[i] = [i**0.5, i**2]
        >>> len(myDB)
        100
        >>> myDB.clear()
        ShareDB instantiated from ./test_clear.ShareDB/.
        >>> len(myDB)
        0
        >>> for i in range(100): myDB[i] = [i**0.5, i**2]
        >>> len(myDB)
        100
        >>> myDB.clear().length()
        0
        >>> myDB.ALIVE
        True
        >>> myDB.close()
        >>> myDB.ALIVE
        False
        >>> shutil.rmtree(myDB.PATH)
        '''
        if self.ALIVE:
            with self.DB.begin(write=True) as dropper:
                to_drop = self.DB.open_db()
                dropper.drop(db=to_drop, delete=False)
        return self

    def close(self):
        '''
        User function to save and close ShareDB instance if unclosed.

        close test cases.

        >>> myDB = ShareDB(path='./test_close.ShareDB', reset=True)
        >>> for i in range(10): myDB[range(i, i+5)] = range(i+5, i+10)
        >>> len(myDB)
        10
        >>> myDB.close()
        >>> myDB = ShareDB(path='./test_close.ShareDB', reset=False)
        >>> len(myDB)
        10
        >>> assert len(myDB.clear()) == 0
        >>> shutil.rmtree(myDB.PATH)
        '''
        if self.ALIVE:
            self.sync()
            self.DB.close()
            self.ALIVE = False
        return None

    def drop(self):
        # TODO
        pass

def get_string(length):
    return ''.join(random.choice('ATGC') for _ in xrange(length))

def populate_dict(dictionary, items):
    population = []
    total_time = 0.
    # local_cach = {}
    for i in xrange(items):
        item = get_string(length=25)
        t0 = time.time()
        population.append(item)
        # dictionary[item] = [random.randint(1, 4000),
        #                     random.randint(1, 4000),
        #                     random.randint(1, 4000)]
        dictionary[item] = 0
        total_time += time.time() - t0
        # if len(local_cach) == 10**6:
        #     dictionary.multiset(local_cach.iteritems())
        #     local_cach = {}
        if random.random() < 0.001:
            print 'WRITER - throughput @ {} writes/second | Filled {}'.format(i/total_time, len(dictionary))
    return population

def worker_process(path, population, pid):
    print 'ENTERED PID {} .. will PROCESS {} items'.format(pid, len(population))
    dictionary = ShareDB(path='./test.ShareDB', reset=False)
    # dictionary = LevelDict(path='./test.ShareDB')
    t0 = time.time()
    total_time = 0.
    # random.shuffle(population)
    for i, item in enumerate(population):
        t0  = time.time()
        # assert item in dictionary
        val = dictionary[item]
        # assert isinstance(val, int)
        # assert val == 0
        # dictionary[item] = val + 1
        # dictionary.sync()

        # assert dictionary[item] == val+1
        total_time += time.time() - t0
        if random.random() < 0.001:
            print 'PID {} - throughput @ {} queries/second | Remaining {}'.format(pid, i/total_time, len(dictionary)-i-1)
            # time.sleep(0.01)

def main():
    dictionary = ShareDB(path='./test.ShareDB', reset=True) # vedis.Vedis('./test.ShareDB')
    # print dir(dictionary.DB.sync)
    # sys.exit(0)
    # dictionary[['KEY']] = 'SOME_VALUE'
    # dictionary['NAME']    = 'Ayaan'
    # dictionary['SURNAME'] = 'Hossain'
    # assert 'NAME' in dictionary
    # assert dictionary['NAME'] == 'Ayaan'
    # assert len(dictionary) == 2
    # dictionary.remove('NAME')
    # assert not 'NAME' in dictionary
    # assert 'SURNAME' in dictionary
    # 
    # print dictionary.BUFFER
    population = populate_dict(dictionary=dictionary, items=1000000)
    # print len(dictionary.BUFFER)
    # print len(dictionary)
    dictionary.close()
    del dictionary
    dictionary = None
    # # worker_process(dictionary, population, pid=0)
    print '\n WRITE FINISHED \n'

    time.sleep(5)

    # sys.exit(0)

    # pool = multiprocessing.Pool(7)
    # params = []
    # for pid in xrange(7):
    #     params.append((dictionary, population, pid))
    # pool.map_async(worker_process, params)
    # pool.close()

    workers = []
    for pid in xrange(7):
        worker = multiprocessing.Process(target=worker_process, args=('./test.ShareDB', population, pid, ))
        workers.append(worker)
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    print '\n READ FINISHED \n'

    shutil.rmtree('./test.ShareDB')

    # dictionary = ShareDB(path='./test.ShareDB', reset=False)
    # cnt = collections.defaultdict(int)
    # pnt = 0
    # for key in population:
    #     if not key in dictionary:
    #         pnt += 1
    #     if dictionary[key] < 7:
    #         cnt[dictionary[key]] += 1
    # print cnt, pnt

    # print '\n ANALYSIS FINISHED \n'

def run_tests():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    # main()
    run_tests()