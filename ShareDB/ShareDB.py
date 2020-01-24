import shutil
import os
import numbers
import msgpack
import pickle
import configparser
import lmdb


class ShareDB(object):
    __license__ = '''
    MIT License

    Copyright (c) 2019-2020 Ayaan Hossain

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

    __doc__ = '''
    ShareDB is a lightweight, persistent key-value store with a dictionary-like interface
    built on top of LMDB. It is intended to replace a python dictionary when

    (1) the key-value store needs to persist locally for later reuse,
    (2) the data needs to be read across multiple processes with minimal overhead, and
    (3) the keys and values can be (de)serialized via msgpack or pickle.

    Sending a ShareDB object to children processes is fine, or you may open the same 
    ShareDB instance in parellel for reading. Parallel writes made in children processes
    are not safe; they are not guaranteed to be written, and may corrupt instance.
    ShareDB is primarily developed and tested using Linux and is compatible with both
    Python 2.7 and 3.8.
    '''

    __version__ = '0.3.7'

    __author__  = 'Ayaan Hossain'

    def __init__(self, path=None, reset=False, serial='msgpack', readers=100, buffer_size=10**5, map_size=10**9):
        '''
        ShareDB constructor.

        :: path        - a/path/to/a/directory/to/persist/the/data (default=None)
        :: reset       - boolean, if True - delete and recreate path following parameters (default=False)
        :: serial      - string, must be either 'msgpack' or 'pickle' (default='msgpack')
        :: readers     - max no. of processes that'll read data in parallel (default=40 processes)
        :: buffer_size - max no. of commits after which a sync is triggered (default=100,000)
        :: map_size    - max amount of bytes to allocate for storage (default=1GB)

        __init__ test cases.

        >>> myDB = ShareDB()
        Traceback (most recent call last):
        TypeError: Given path=None of <type 'NoneType'>,
                         reset=False of <type 'bool'>,
                         serial=msgpack of <type 'str'>,
                         readers=100 of <type 'int'>,
                         buffer_size=100000 of <type 'int'>,
                         map_size=1000000000 of <type 'int'>,
                         raised: 'NoneType' object has no attribute 'endswith'
        >>> myDB = ShareDB(path=True)
        Traceback (most recent call last):
        TypeError: Given path=True of <type 'bool'>,
                         reset=False of <type 'bool'>,
                         serial=msgpack of <type 'str'>,
                         readers=100 of <type 'int'>,
                         buffer_size=100000 of <type 'int'>,
                         map_size=1000000000 of <type 'int'>,
                         raised: 'bool' object has no attribute 'endswith'
        >>> myDB = ShareDB(path=123)
        Traceback (most recent call last):
        TypeError: Given path=123 of <type 'int'>,
                         reset=False of <type 'bool'>,
                         serial=msgpack of <type 'str'>,
                         readers=100 of <type 'int'>,
                         buffer_size=100000 of <type 'int'>,
                         map_size=1000000000 of <type 'int'>,
                         raised: 'int' object has no attribute 'endswith'
        >>> myDB = ShareDB(path='/22.f')
        Traceback (most recent call last):
        TypeError: Given path=/22.f.ShareDB/ of <type 'str'>,
                         reset=False of <type 'bool'>,
                         serial=msgpack of <type 'str'>,
                         readers=100 of <type 'int'>,
                         buffer_size=100000 of <type 'int'>,
                         map_size=1000000000 of <type 'int'>,
                         raised: [Errno 13] Permission denied: '/22.f.ShareDB/'
        >>> myDB = ShareDB(path='./test_init.ShareDB', reset=True, serial='something_fancy')
        Traceback (most recent call last):
        TypeError: Given path=./test_init.ShareDB/ of <type 'str'>,
                         reset=True of <type 'bool'>,
                         serial=something_fancy of <type 'str'>,
                         readers=100 of <type 'int'>,
                         buffer_size=100000 of <type 'int'>,
                         map_size=1000000000 of <type 'int'>,
                         raised: serial must be 'msgpack' or 'pickle' not something_fancy
        >>> myDB = ShareDB(path='./test_init.ShareDB', reset=True, readers='XYZ', buffer_size=100, map_size=10**3)
        Traceback (most recent call last):
        TypeError: Given path=./test_init.ShareDB/ of <type 'str'>,
                         reset=True of <type 'bool'>,
                         serial=msgpack of <type 'str'>,
                         readers=XYZ of <type 'str'>,
                         buffer_size=100 of <type 'int'>,
                         map_size=1000 of <type 'int'>,
                         raised: invalid literal for int() with base 10: 'XYZ'
        >>> myDB = ShareDB(path='./test_init.ShareDB', reset=True, readers=40, buffer_size=100, map_size=10**3)
        >>> myDB.PATH
        './test_init.ShareDB/'
        >>> myDB.ALIVE
        True
        >>> myDB.PARALLEL
        40
        >>> myDB.BCSIZE
        100
        >>> myDB.BQSIZE
        0
        >>> myDB.MSLIMIT
        1000
        >>> len(myDB) == 0
        True
        >>> myDB.drop()
        True
        '''
        try:
            # Format path correctly
            path = self._trim_suffix(given_str=path, suffix='/')
            path = self._trim_suffix(given_str=path, suffix='.ShareDB')
            path += '.ShareDB/'

            # Reset ShareDB instance if necessary
            if reset:
                self._clear_path(path)

            # Create path if absent
            if not os.path.isdir(path):
                os.makedirs(path)

            # Create configuration if absent
            if not os.path.exists(path + 'ShareDB.config'):
                config = self._store_config(
                    path, serial, buffer_size, map_size, readers)
            # Otherwise load configuration
            else:
                config = self._load_config(path)

            # Setup ShareDB instance
            self.PATH  = path  # Path to ShareDB
            self.ALIVE = True  # Instance is alive
            # Serialization to use for (un)packing keys and values
            self.PACK, self.UNPACK = self._get_serialization_functions(
                serial=config.get('ShareDB Config', 'SERIAL'))
            # Number of processes reading in parallel
            self.PARALLEL = config.getint('ShareDB Config', 'PARALLEL')
            # Trigger sync after this many items inserted
            self.BCSIZE = config.getint('ShareDB Config', 'BCSIZE')
            # Approx. no. of items to sync in ShareDB
            self.BQSIZE = config.getint('ShareDB Config', 'BQSIZE')
            # Memory map size, maybe larger than RAM
            self.MSLIMIT = config.getint('ShareDB Config', 'MSLIMIT')
            self.DB = lmdb.open(
                self.PATH,
                subdir=True,
                map_size=self.MSLIMIT,
                create=True,
                readahead=False,
                writemap=True,
                map_async=True,
                max_readers=self.PARALLEL,
                max_dbs=0,
                lock=True)

        except Exception as E:
            raise TypeError(
                '''Given path={} of {},
                 reset={} of {},
                 serial={} of {},
                 readers={} of {},
                 buffer_size={} of {},
                 map_size={} of {},
                 raised: {}'''.format(
                    path,        type(path),
                    reset,       type(reset),
                    serial,      type(serial),
                    readers,     type(readers),
                    buffer_size, type(buffer_size),
                    map_size,    type(map_size),
                    E))

    @staticmethod
    def _trim_suffix(given_str, suffix):
        '''
        Internal helper function to trim suffixes in given_str.
        '''
        if given_str.endswith(suffix):
            return given_str[:-len(suffix)]
        return given_str

    @staticmethod
    def _clear_path(path):
        '''
        Internal helper function to clear given path.
        '''
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.exists(path):
            os.remove(path)

    @staticmethod
    def _store_config(path, serial, buffer_size, map_size, readers):
        '''
        Internal helper funtion to create ShareDB configuration file.
        '''
        config = configparser.RawConfigParser()
        config.add_section('ShareDB Config')
        config.set('ShareDB Config', 'SERIAL',   serial)
        config.set('ShareDB Config', 'PARALLEL', readers)
        config.set('ShareDB Config', 'BCSIZE',   buffer_size)
        config.set('ShareDB Config', 'BQSIZE',   0)
        config.set('ShareDB Config', 'MSLIMIT',  map_size)
        with open(path + 'ShareDB.config', 'w') as config_file:
            config.write(config_file)
        return config

    @staticmethod
    def _load_config(path):
        '''
        Internal helper funtion to load ShareDB configuration file.
        '''
        config = configparser.RawConfigParser()
        config.read(path+'ShareDB.config')
        return config

    @staticmethod
    def _get_serialization_functions(serial):
        '''
        Internal helper function to decide (un)packing functions.
        '''
        if serial not in ['msgpack', 'pickle']:
            raise ValueError(
                'serial must be \'msgpack\' or \'pickle\' not {}'.format(serial))
        if serial == 'msgpack':
            PACK   = lambda x: msgpack.packb(x, use_bin_type=True)
            UNPACK = lambda x: msgpack.unpackb(x, raw=False, use_list=True)
        if serial == 'pickle':
            PACK   = lambda x: pickle.dumps(x, protocol=pickle.HIGHEST_PROTOCOL)
            UNPACK = lambda x: pickle.loads(x)
        return PACK, UNPACK

    def alivemethod(method):
        '''
        Internal decorator gating ShareDB operations when instance is closed/dropped.
        '''
        def wrapper(self, *args, **kwargs):
            if self.ALIVE:
                return method(self, *args, **kwargs)
            else:
                raise RuntimeError(
                    'Access to {} has been closed or dropped'.format(repr(self)))
        return wrapper

    def __repr__(self):
        '''
        Pythonic dunder function to return a string representation of ShareDB instance.

        __repr__ test cases.

        >>> myDB = ShareDB(path='./test_repr.ShareDB', reset=True)
        >>> myDB
        ShareDB instantiated from ./test_repr.ShareDB/
        >>> myDB.drop()
        True
        '''
        return 'ShareDB instantiated from {}'.format(self.PATH)

    def __str__(self):
        '''
        Pythonic dunder function to return a string representation of ShareDB instance.

        __str__ test cases.

        >>> myDB = ShareDB(path='./test_str.ShareDB', reset=True)
        >>> myDB
        ShareDB instantiated from ./test_str.ShareDB/
        >>> myDB.drop()
        True
        '''
        return repr(self)

    def _get_packed_key(self, key):
        '''
        Internal helper function to try and pack given key.

        :: key - a valid key to be inserted/updated in ShareDB

        _get_packed_key test cases.

        >>> myDB = ShareDB(path='./test_get_packed_key', reset=True)
        >>> test_key = [1, '2', 3.0, None]
        >>> myDB._get_packed_key(key=test_key) == msgpack.packb(test_key, use_bin_type=True)
        True
        >>> myDB._get_packed_key(key=set(test_key[:1]))
        Traceback (most recent call last):
        TypeError: Given key=set([1]) of <type 'set'>, raised: can not serialize 'set' object
        >>> myDB._get_packed_key(key=None)
        Traceback (most recent call last):
        TypeError: ShareDB cannot use <type 'NoneType'> objects as keys
        >>> myDB.drop()
        True
        '''
        if key is None:
            raise TypeError(
                'ShareDB cannot use {} objects as keys'.format(type(None)))
        try:
            key = self.PACK(key)
        except Exception as E:
            raise TypeError(
                'Given key={} of {}, raised: {}'.format(
                    key, type(key), E))
        return key

    def _get_unpacked_key(self, key):
        '''
        Internal helper function to try and unpack given key.

        :: key - a valid key to be inserted/updated in ShareDB

        _get_packed_key test cases.

        >>> myDB = ShareDB(path='./test_get_unpacked_key.ShareDB', reset=True)
        >>> test_key = [1, '2', 3.0, None]
        >>> myDB._get_unpacked_key(key=myDB._get_packed_key(key=test_key)) == test_key
        True
        >>> myDB.drop()
        True
        '''
        if key is None:
            raise TypeError(
                'ShareDB cannot use {} objects as keys'.format(type(None)))
        try:
            key = self.UNPACK(key)
        except Exception as E:
            raise TypeError(
                'Given key={} of {}, raised: {}'.format(
                    key, type(key), E))
        return key

    def _get_packed_val(self, val):
        '''
        Internal helper function to try and pack given value.

        :: val - a valid value/object associated with given key

        _get_packed_val test cases.

        >>> myDB = ShareDB(path='./test_get_packed_val.ShareDB', reset=True)
        >>> test_val = {0: [1, '2', 3.0, None]}
        >>> myDB._get_packed_val(val=test_val) == msgpack.packb(test_val, use_bin_type=True)
        True
        >>> myDB._get_packed_val(val=set(test_val[0][:1]))
        Traceback (most recent call last):
        TypeError: Given value=set([1]) of <type 'set'>, raised: can not serialize 'set' object
        >>> myDB._get_packed_val(val=None)
        Traceback (most recent call last):
        TypeError: ShareDB cannot use <type 'NoneType'> objects as values
        >>> myDB.drop()
        True
        '''
        if val is None:
            raise TypeError(
                'ShareDB cannot use {} objects as values'.format(type(None)))
        try:
            val = self.PACK(val)
        except Exception as E:
            raise TypeError(
                'Given value={} of {}, raised: {}'.format(
                    val, type(val), E))
        return val

    def _get_unpacked_val(self, val):
        '''
        Internal helper function to try and unpack given value.

        :: val - a valid value/object associated with given key

        _get_packed_val test cases.

        >>> myDB = ShareDB(path='./test_get_unpacked_val.ShareDB', reset=True)
        >>> test_val = {0: [1, '2', 3.0, None]}
        >>> myDB._get_unpacked_val(val=myDB._get_packed_val(val=test_val)) == test_val
        True
        >>> myDB.drop()
        True
        '''
        if val is None:
            raise TypeError(
                'ShareDB cannot use {} objects as values'.format(type(None)))
        try:
            val = self.UNPACK(val)
        except Exception as E:
            raise TypeError(
                'Given value={} of {}, raised: {}'.format(
                    val, type(val), E))
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
        try:
            txn.put(key=key, value=val, overwrite=True, append=False)
        except lmdb.MapFullError:
            raise MemoryError(
                '{} is full'.format(str(self)))
        except Exception as E:
            raise TypeError(
                'Given key={} of {} and value={} of {} raised: {}'.format(
                    key, type(key), val, type(val), E))
        self.BQSIZE += 1
        self._trigger_sync()
        return None

    @alivemethod
    def set(self, key, val):
        '''
        User function to insert/overwrite a key-value pair into ShareDB instance.

        :: key - a valid key to be inserted/updated in ShareDB
        :: val - a valid value/object associated with given key

        set test cases.d

        >>> myDB = ShareDB(path='./test_set.ShareDB', reset=True)
        >>> myDB.set(key=('NAME'), val='Ayaan Hossain')
        ShareDB instantiated from ./test_set.ShareDB/
        >>> myDB.set(key=['KEY'], val=set(['SOME_VALUE']))
        Traceback (most recent call last):
        TypeError: Given value=set(['SOME_VALUE']) of <type 'set'>, raised: can not serialize 'set' object
        >>> myDB.set(key=(1, 2, 3, 4), val='SOME_VALUE')
        ShareDB instantiated from ./test_set.ShareDB/
        >>> myDB.set(key='ANOTHER KEY', val=[1, 2, 3, 4])
        ShareDB instantiated from ./test_set.ShareDB/
        >>> myDB.drop()
        True
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
        TypeError: Given key=set(['KEY']) of <type 'set'>, raised: can not serialize 'set' object
        >>> myDB.drop()
        True
        '''
        return self.set(key=key, val=val)

    @alivemethod
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
        ShareDB instantiated from ./test_multi_set.ShareDB/
        >>> len(myDB)
        15
        >>> for i in range(3005, 3010): myDB[tuple(range(i, i+5))] = range(i+5, i+10)
        >>> len(myDB)
        20
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_multi_set.ShareDB', reset=False)
        >>> len(myDB)
        20
        >>> myDB[tuple(range(3005, 3010))] == range(3010, 3015)
        True
        >>> myDB[tuple(range(1))] = set(range(1))
        Traceback (most recent call last):
        TypeError: Given value=set([0]) of <type 'set'>, raised: can not serialize 'set' object
        >>> myDB[set(range(1))] = range(1)
        Traceback (most recent call last):
        TypeError: Given key=set([0]) of <type 'set'>, raised: can not serialize 'set' object
        >>> myDB.drop()
        True
        '''
        with self.DB.begin(write=True) as kvsetter:
            try:
                for key, val in kv_iter:
                    self._insert_kv_in_txn(key=key, val=val, txn=kvsetter)
            except Exception as E:
                raise Exception(
                    'Given kv_iter={} of {}, raised: {}'.format(
                        kv_iter, type(kv_iter), E))
        return self

    def _get_val_on_disk(self, key, txn, packed=False, default=None):
        '''
        Internal helper function to return the packed value associated with given key.

        :: key     - a valid key to query ShareDB for associated value
        :: txn     - a transaction interface for query
        :: packed  - boolean, if True - will attempt packing key (default=False)
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
        :: packed  - boolean, if True - will attempt packing key (default=False)
        :: default - a default value to return when key is absent (default=None)
        '''
        val = self._get_val_on_disk(
            key=key, txn=txn, packed=packed, default=default)
        if val is default:
            return default
        return self._get_unpacked_val(val)

    @alivemethod
    def get(self, key, default=None):
        '''
        User function to query value for a given key else return default.

        :: key     - a valid key to query ShareDB for associated value
        :: default - a default value to return when key is absent (default=None)

        get test cases.

        >>> myDB = ShareDB(path='./test_get_dunder.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = i**0.5
        >>> len(myDB)
        100
        >>> myDB = ShareDB(path='./test_get_dunder.ShareDB', reset=False)
        >>> for i in range(100): assert myDB.get(i) == i**0.5
        >>> myDB.get(key=81)
        9.0
        >>> myDB.get(key=202, default='SENTINEL')
        'SENTINEL'
        >>> myDB.clear()
        ShareDB instantiated from ./test_get_dunder.ShareDB/
        >>> myDB.get(key=81, default='SENTINEL')
        'SENTINEL'
        >>> myDB.get(key=81)
        >>> myDB.drop()
        True
        '''
        with self.DB.begin(write=False) as kvgetter:
            val = self._get_unpacked_val_on_disk(
                key=key, txn=kvgetter, packed=False, default=default)
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
        True
        >>> myDB = ShareDB(path='./test_getitem', reset=False)
        >>> myDB[49]
        7.0
        >>> myDB[49.0]
        Traceback (most recent call last):
        KeyError: "key=49.0 of <type 'float'> is absent"
        >>> myDB[set([49.0])]
        Traceback (most recent call last):
        TypeError: Given key=set([49.0]) of <type 'set'>, raised: can not serialize 'set' object
        >>> myDB.drop()
        True
        '''
        val = self.get(key=key, default=None)
        if val is None:
            raise KeyError(
                'key={} of {} is absent'.format(key, type(key)))
        return val

    @alivemethod
    def multiget(self, key_iter, default=None):
        '''
        User function to return an iterator of values for a given iterable of keys.

        :: key_iter - a valid iterable of keys to query ShareDB for values
        :: default  - a default value to return when key is absent in ShareDB (default=None)

        multiget test cases.

        >>> myDB = ShareDB(path='./test_multiget.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = i**2
        >>> len(myDB)
        100
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_multiget.ShareDB', reset=False)
        >>> len(list(myDB.multiget(key_iter=range(100), default=None))) == 100
        True
        >>> myDB.multiget(key_iter=range(100, 110), default=False).next()
        False
        >>> myDB.multiget(key_iter=[None]).next()
        Traceback (most recent call last):
        Exception: Given key_iter=[None] of <type 'list'>, raised: ShareDB cannot use <type 'NoneType'> objects as keys
        >>> myDB.drop()
        True
        '''
        with self.DB.begin(write=False) as kvgetter:
            try:
                for key in key_iter:
                    yield self._get_unpacked_val_on_disk(
                        key=key, txn=kvgetter, packed=False, default=default)
            except Exception as E:
                raise Exception(
                    'Given key_iter={} of {}, raised: {}'.format(
                        key_iter, type(key_iter), E))

    @alivemethod
    def has_key(self, key):
        '''
        User function to check existence of given key in ShareDB.

        :: key - a candidate key potentially in ShareDB

        has_key test cases.

        >>> myDB = ShareDB(path='./test_has_key', reset=True)
        >>> myDB.multiset((i, [i**0.5, i**2.0]) for i in range(100, 200))
        ShareDB instantiated from ./test_has_key.ShareDB/
        >>> len(myDB)
        100
        >>> myDB.has_key(150)
        True
        >>> myDB.clear().has_key(150)
        False
        >>> myDB.multiset(((i,[i**0.5, i**2.0]) for i in range(100))).has_key(49)
        True
        >>> myDB.drop()
        True
        '''
        with self.DB.begin(write=False) as kvgetter:
            val = self._get_val_on_disk(
                key=key, txn=kvgetter, packed=False, default=None)
        if val is None:
            return False
        return True

    def __contains__(self, key):
        '''
        Pythonic dunder function to check existence of given key in ShareDB.

        :: key - a candidate key potentially in ShareDB

        ___contain___ test cases.

        >>> myDB = ShareDB(path='./test_contains', reset=True, serial='pickle')
        >>> for i in range(100): myDB[i] = [i**0.5, i**2]
        >>> 95 in myDB
        True
        >>> 1 in myDB
        True
        >>> 16**6 in myDB
        False
        >>> myDB.close()
        True
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
        >>> myDB.drop()
        True
        '''
        return self.has_key(key=key)

    @alivemethod
    def length(self):
        '''
        User function to return the number of items stored in ShareDB.

        length test cases.

        >>> myDB = ShareDB(path='./test_length', reset=True, serial='pickle')
        >>> for i in range(500, 600): myDB[i] = set([2.0*i])
        >>> len(myDB)
        100
        >>> myDB.sync().clear().length()
        0
        >>> myDB.drop()
        True
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
        True
        >>> myDB = ShareDB(path='./test_len.ShareDB', reset=False)
        >>> len(myDB)
        100
        >>> myDB.clear()
        ShareDB instantiated from ./test_len.ShareDB/
        >>> len(myDB)
        0
        >>> myDB.drop()
        True
        '''
        return self.length()

    def _del_pop_from_disk(self, key, txn, opr, packed=False):
        '''
        Internal helper function to delete/pop key-value pair via txn and trigger sync.

        :: key    - a candidate key potentially in ShareDB
        :: txn    - a transaction interface for delete/pop
        :: opr    - string, must be 'del' or 'pop' specifying the operation
        :: packed - boolean, if True - will attempt packing key (default=False)
        '''
        if not packed:
            key = self._get_packed_key(key=key)
        if opr == 'del':
            txn.delete(key=key)
            val = None
        elif opr == 'pop':
            try:
                val = self._get_unpacked_val(val=txn.pop(key=key))
            except:
                key = self._get_unpacked_key(key=key)
                raise KeyError(
                    'key={} of {} is absent'.format(
                        key, type(key)))
        else:
            raise ValueError(
                'opr must be \'del\' or \'pop\' not {}'.format(opr))
        self.BQSIZE += 1
        self._trigger_sync()
        return val

    @alivemethod
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
        True
        >>> myDB = ShareDB(path='./test_remove', reset=False)
        >>> myDB.remove(99).length()
        99
        >>> 99 in myDB
        False
        >>> myDB.drop()
        True
        '''
        with self.DB.begin(write=True) as keydeler:
            self._del_pop_from_disk(
                key=key, txn=keydeler, opr='del', packed=False)
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
        True
        >>> myDB = ShareDB(path='./test_delitem', reset=False)
        >>> del myDB[99]
        >>> 99 in myDB
        False
        >>> myDB.drop()
        True
        '''
        return self.remove(key=key)

    @alivemethod
    def multiremove(self, key_iter):
        '''
        User function to remove all key-value pairs specified in the iterable of keys.

        :: key_iter - a valid iterable of keys to be deleted from ShareDB

        multiremove test cases.

        >>> myDB = ShareDB(path='./test_multiremove.ShareDB', reset=True, serial='pickle')
        >>> for i in range(100): myDB[i] = i**2
        >>> len(myDB)
        100
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_multiremove.ShareDB', reset=False)
        >>> myDB.multiremove(range(100)).length()
        0
        >>> 0 in myDB
        False
        >>> myDB.drop()
        True
        '''
        with self.DB.begin(write=True) as keydeler:
            try:
                for key in key_iter:
                    self._del_pop_from_disk(
                        key=key, txn=keydeler, opr='del', packed=False)
            except Exception as E:
                raise Exception(
                    'Given key_iter={} of {}, raised: {}'.format(
                        key_iter, type(key_iter), E))
        return self

    @alivemethod
    def pop(self, key):
        '''
        User function to pop a key and return its value.

        :: key - a valid key to be deleted from ShareDB

        pop test cases.

        >>> myDB = ShareDB(path='./test_pop.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = [i**0.5]
        >>> len(myDB)
        100
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_pop', reset=False)
        >>> myDB.pop(49)
        [7.0]
        >>> 49 in myDB
        False
        >>> len(myDB)
        99
        >>> myDB.pop(49)
        Traceback (most recent call last):
        KeyError: "key=49 of <type 'int'> is absent"
        >>> myDB.drop()
        True
        '''
        with self.DB.begin(write=True) as keypopper:
            val = self._del_pop_from_disk(
                key=key, txn=keypopper, opr='pop', packed=False)
        return val

    @alivemethod
    def multipop(self, key_iter):
        '''
        User function to return an iterator of popped values for a given iterable of keys.

        :: key_iter - a valid iterable of keys to be deleted from ShareDB

        multipop test cases.

        >>> myDB = ShareDB(path='./test_multipop.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = [i**0.5]
        >>> len(myDB)
        100
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_multipop', reset=False)
        >>> pop_iter = myDB.multipop(range(49, 74))
        >>> pop_iter.next()
        [7.0]
        >>> len(list(pop_iter))
        24
        >>> len(myDB)
        75
        >>> pop_iter = myDB.multipop([199, 200])
        >>> pop_iter.next()
        Traceback (most recent call last):
        Exception: Given key_iter=[199, 200] of <type 'list'>, raised: "key=199 of <type 'int'> is absent"
        >>> myDB.drop()
        True
        '''
        with self.DB.begin(write=True) as keypopper:
            try:
                for key in key_iter:
                    yield self._del_pop_from_disk(
                        key=key, txn=keypopper, opr='pop', packed=False)
            except Exception as E:
                raise Exception(
                    'Given key_iter={} of {}, raised: {}'.format(
                        key_iter, type(key_iter), E))

    def _iter_on_disk_kv(self, yield_key=False, unpack_key=False, yield_val=False, unpack_val=False):
        '''
        Internal helper function to iterate over key and/or values in ShareDB.

        :: yield_key  - boolean, if True will stream keys
        :: unpack_key - boolean, if True will un-msgpack keys
        :: yield_val  - boolean, if True will stream values
        :: unpack_val - boolean, if True will un-msgpack values

        _iter_on_disk_kv test cases.

        >>> myDB = ShareDB(path='./test_iter_on_disk_kv.ShareDB', reset=True)
        >>> myDB.multiset((i,i**2) for i in range(10)).length()
        10
        >>> len(list(myDB._iter_on_disk_kv(1,0,0,0)))
        10
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_iter_on_disk_kv', reset=False)
        >>> len(list(myDB._iter_on_disk_kv(0,0,1,0)))
        10
        >>> 9 in myDB
        True
        >>> 10 in myDB
        False
        >>> myDB.drop()
        True
        '''
        with self.DB.begin(write=False) as kviter:
            with kviter.cursor() as kvcursor:
                for key, val in kvcursor:
                    if unpack_key:
                        key = self._get_unpacked_key(key=key)
                    if unpack_val:
                        val = self._get_unpacked_val(val=val)
                    if yield_key and not yield_val:
                        yield key
                    elif yield_val and not yield_key:
                        yield val
                    elif yield_key and yield_val:
                        yield key, val
                    else:
                        raise ValueError(
                            'All args to ._iter_on_disk_kv() are False or None')

    @alivemethod
    def items(self):
        '''
        User function to iterate over key-value pairs in ShareDB.

        items test cases.

        >>> myDB = ShareDB(path='./test_items.ShareDB', reset=True)
        >>> myDB.multiset((i,i**2) for i in range(10)).length()
        10
        >>> len(list(myDB.items()))
        10
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_items', reset=False)
        >>> 9 in myDB
        True
        >>> 10 in myDB
        False
        >>> myDB.drop()
        True
        '''
        return self._iter_on_disk_kv(
            yield_key=True, unpack_key=True, yield_val=True, unpack_val=True)

    @alivemethod
    def keys(self):
        '''
        User function to iterate over keys in ShareDB.

        keys test cases.

        >>> myDB = ShareDB(path='./test_keys.ShareDB', reset=True)
        >>> myDB.multiset((i,i**2) for i in range(10)).length()
        10
        >>> len(list(myDB.keys()))
        10
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_keys', reset=False)
        >>> 9 in myDB
        True
        >>> 10 in myDB
        False
        >>> myDB.drop()
        True
        '''
        return self._iter_on_disk_kv(yield_key=True, unpack_key=True)

    @alivemethod
    def __iter__(self):
        '''
        Pythonic dunder function to iterate over keys in ShareDB.

        __iter__ test cases.

        >>> myDB = ShareDB(path='./test_iter.ShareDB', reset=True)
        >>> myDB.multiset((i,i**2) for i in range(10)).length()
        10
        >>> sorted(iter(myDB))
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> for key in myDB: assert myDB[key] == key**2
        >>> 10 in iter(myDB)
        False
        >>> myDB.drop()
        True
        '''
        return self.keys()

    @alivemethod
    def values(self):
        '''
        User function to iterate over values in ShareDB.

        values test cases.

        >>> myDB = ShareDB(path='./test_values.ShareDB', reset=True)
        >>> myDB.multiset((i,i**2) for i in range(10)).length()
        10
        >>> len(list(myDB.values()))
        10
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_values', reset=False)
        >>> 9 in myDB
        True
        >>> 10 in myDB
        False
        >>> myDB.drop()
        True
        '''
        return self._iter_on_disk_kv(yield_val=True, unpack_val=True)

    @alivemethod
    def popitem(self):
        '''
        User function to pop a single key-value pairs in ShareDB.

        popitem test cases.

        >>> myDB = ShareDB(path='./test_popitem.ShareDB', reset=True)
        >>> myDB.multiset((i,i**2) for i in range(10, 20)).length()
        10
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_popitem', reset=False)
        >>> myDB.popitem()
        (10, 100)
        >>> myDB.drop()
        True
        '''
        curr_key = self._iter_on_disk_kv(yield_key=True, unpack_key=False)
        item_key = next(curr_key)
        with self.DB.begin(write=True) as itempopper:
            key, val = self._get_unpacked_key(key=item_key), \
                       self._del_pop_from_disk(
                            key=item_key, txn=itempopper, opr='pop', packed=True)
        return key, val

    @alivemethod
    def multipopitem(self, num_items=None):
        '''
        User function to pop over key-value pairs in ShareDB.

        :: num_items - an integer specifying the maximum number of items to pop

        multpopitem test cases.

        >>> myDB = ShareDB(path='./test_multpopitem.ShareDB', reset=True)
        >>> myDB.multiset((i,i**2) for i in range(10)).length()
        10
        >>> len(list(myDB.keys()))
        10
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_multpopitem', reset=False)
        >>> len(list(myDB.multipopitem(num_items='THIS IS NOT A NUMBER')))
        Traceback (most recent call last):
        TypeError: num_items=THIS IS NOT A NUMBER of <type 'str'> must be an integer/long/float
        >>> len(list(myDB.multipopitem(num_items=len(myDB)*1.0)))
        10
        >>> 1 in myDB
        False
        >>> len(list(myDB.multiset((i,i**2) for i in range(10)).multipopitem(num_items=15)))
        10
        >>> myDB.drop()
        True
        '''
        # Check if num_items is valid, and set up accordingly
        if not isinstance(num_items, numbers.Real):
            raise TypeError(
                'num_items={} of {} must be an integer/long/float'.format(
                    num_items, type(num_items)))

        # Iterate over ShareDB and load num_item keys in packed state
        num_items = min(num_items, self.length()) # safe upper limit
        curr_key  = self._iter_on_disk_kv(yield_key=True, unpack_key=False)
        item_keys = []
        while len(item_keys) < num_items:
            item_keys.append(next(curr_key))

        # Pop packed keys in item_keys, and yield the unapacked items
        with self.DB.begin(write=True) as itempopper:
            for item_key in item_keys:
                yield self._get_unpacked_key(key=item_key), \
                    self._del_pop_from_disk(
                        key=item_key, txn=itempopper, opr='pop', packed=True)

    @alivemethod
    def sync(self):
        '''
        User function to flush ShareDB inserts/changes/commits on to disk.
        '''
        self.DB.sync()
        return self

    def _delete_keys_and_db(self, drop_DB):
        '''
        Internal helper function to delete keys and drop database.

        :: drop_DB - boolean, if True - will delete the database
        '''
        with self.DB.begin(write=True) as dropper:
            to_drop = self.DB.open_db()
            dropper.drop(db=to_drop, delete=drop_DB)

    @alivemethod
    def clear(self):
        '''
        User function to remove all data stored in a ShareDB instance.

        clear test cases.

        >>> myDB = ShareDB(path='./test_clear/', reset=True)
        >>> for i in range(100): myDB[i] = [i**0.5, i**2]
        >>> len(myDB)
        100
        >>> myDB.clear()
        ShareDB instantiated from ./test_clear.ShareDB/
        >>> len(myDB)
        0
        >>> for i in range(100): myDB[i] = [i**0.5, i**2]
        >>> len(myDB)
        100
        >>> myDB.clear().length()
        0
        >>> for i in range(100): myDB[i] = [i**0.5, i**2]
        >>> len(myDB)
        100
        >>> myDB.drop()
        True
        '''
        self._delete_keys_and_db(drop_DB=False)
        return self

    def close(self):
        '''
        User function to save and close ShareDB instance if unclosed.

        close test cases.

        >>> myDB = ShareDB(path='./test_close.ShareDB', reset=True)
        >>> for i in range(10): myDB[list(range(i, i+5))] = list(range(i+5, i+10))
        >>> len(myDB)
        10
        >>> myDB.close()
        True
        >>> myDB.close()
        False
        >>> myDB = ShareDB(path='./test_close.ShareDB', reset=False)
        >>> len(myDB)
        10
        >>> assert len(myDB.clear()) == 0
        >>> myDB.close()
        True
        >>> myDB.ALIVE
        False
        >>> 1 in myDB
        Traceback (most recent call last):
        RuntimeError: Access to ShareDB instantiated from ./test_close.ShareDB/ has been closed or dropped
        >>> myDB = ShareDB(path='./test_close.ShareDB', reset=False)
        >>> myDB.drop()
        True
        '''
        if self.ALIVE:
            self.sync()
            self.DB.close()
            self.ALIVE = False
            return True
        return False

    def drop(self):
        '''
        User function to delete a ShareDB instance.

        drop test cases.

        >>> myDB = ShareDB(path='./test_drop.ShareDB', reset=True)
        >>> for i in range(10): myDB[list(range(i, i+5))] = list(range(i+5, i+10))
        >>> len(myDB)
        10
        >>> len(myDB)
        10
        >>> myDB.drop()
        True
        >>> myDB.ALIVE
        False
        >>> 0 in myDB
        Traceback (most recent call last):
        RuntimeError: Access to ShareDB instantiated from ./test_drop.ShareDB/ has been closed or dropped
        >>> myDB = ShareDB(path='./test_drop.ShareDB', reset=False)
        >>> len(myDB)
        0
        >>> myDB.drop()
        True
        '''
        if self.ALIVE:
            self._delete_keys_and_db(drop_DB=True)
            self.close()
            self._clear_path(self.PATH)
            return True
        return False


def main():
    import doctest
    doctest.testmod()


if __name__ == '__main__':
    main()
