import shutil
import os
import numbers
import msgpack
import pickle
import zlib
import configparser
import functools
import lmdb


class ShareDB(object):
    __license__ = """
    MIT License

    Copyright (c) 2019-2026 Ayaan Hossain

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
    """

    __doc__ = """
    ShareDB is a lightweight, persistent key-value store with a dictionary-like interface
    built on top of LMDB. It is intended to replace a python dictionary when

    (1) the key-value information needs to persist locally for later reuse,
    (2) the data needs to be shared across multiple processes with minimal overhead, and
    (3) the keys and values can be (de)serialized via msgpack or pickle.

    A ShareDB instance may be opened simultaneously in children, for reading in parallel,
    while a single parent writes to the instance. Parallel writes made across processes
    are not safe; they are not guaranteed to be written, and may corrupt instance. ShareDB
    is primarily developed and tested using Linux and requires Python 3.8 or above.
    """

    __version__ = "2.0.2"

    __author__ = "Ayaan Hossain"

    _SENTINEL = object()

    def __init__(
        self,
        path,
        reset=False,
        serial="pickle",
        compress=False,
        readers=256,
        buffer_size=10**5,
        map_size=None,
    ):
        """ShareDB constructor.

        Parameters
        ----------
        path : str
            Path to a directory where data will be persisted. The suffix
            ``.ShareDB/`` is appended automatically if not already present.
        reset : bool, optional
            If True, delete and recreate the directory using the parameters
            that follow. Default is False.
        serial : str, optional
            Serialization backend; must be ``'msgpack'`` or ``'pickle'``.
            Default is ``'pickle'``.
        compress : bool, optional
            If True, compress values with zlib before storage. Default is False.
        readers : int, optional
            Maximum number of concurrent read-only processes. Default is 256.
        buffer_size : int, optional
            Number of inserts after which an automatic sync is triggered.
            Default is 100,000.
        map_size : int or None, optional
            Maximum bytes to allocate for storage. Pass None to use all
            available disk space. Default is None.

        Returns
        -------
        ShareDB
            self.

        Raises
        ------
        TypeError
            If any argument is invalid or the database directory cannot
            be created or opened.

        Notes
        -----
        ``None`` is not a valid key or value.

        When ``serial='msgpack'``, tuples are deserialized as lists because
        msgpack does not distinguish between tuple and list.

        Examples
        --------
        >>> myDB = ShareDB(path=None)
        Traceback (most recent call last):
        TypeError: Given path=None of <class 'NoneType'>,
                         reset=False of <class 'bool'>,
                         serial=pickle of <class 'str'>,
                         compress=False of <class 'bool'>,
                         readers=256 of <class 'int'>,
                         buffer_size=100000 of <class 'int'>,
                         map_size=None of <class 'NoneType'>,
                         raised: 'NoneType' object has no attribute 'endswith'
        >>> myDB = ShareDB(path=True)
        Traceback (most recent call last):
        TypeError: Given path=True of <class 'bool'>,
                         reset=False of <class 'bool'>,
                         serial=pickle of <class 'str'>,
                         compress=False of <class 'bool'>,
                         readers=256 of <class 'int'>,
                         buffer_size=100000 of <class 'int'>,
                         map_size=None of <class 'NoneType'>,
                         raised: 'bool' object has no attribute 'endswith'
        >>> myDB = ShareDB(path=123)
        Traceback (most recent call last):
        TypeError: Given path=123 of <class 'int'>,
                         reset=False of <class 'bool'>,
                         serial=pickle of <class 'str'>,
                         compress=False of <class 'bool'>,
                         readers=256 of <class 'int'>,
                         buffer_size=100000 of <class 'int'>,
                         map_size=None of <class 'NoneType'>,
                         raised: 'int' object has no attribute 'endswith'
        >>> myDB = ShareDB(path='/22.f')
        Traceback (most recent call last):
        TypeError: Given path=/22.f.ShareDB/ of <class 'str'>,
                         reset=False of <class 'bool'>,
                         serial=pickle of <class 'str'>,
                         compress=False of <class 'bool'>,
                         readers=256 of <class 'int'>,
                         buffer_size=100000 of <class 'int'>,
                         map_size=None of <class 'NoneType'>,
                         raised: [Errno 13] Permission denied: '/22.f.ShareDB/'
        >>> myDB = ShareDB(path='./test_init.ShareDB', reset=True, serial='something_fancy')
        Traceback (most recent call last):
        TypeError: Given path=./test_init.ShareDB/ of <class 'str'>,
                         reset=True of <class 'bool'>,
                         serial=something_fancy of <class 'str'>,
                         compress=False of <class 'bool'>,
                         readers=256 of <class 'int'>,
                         buffer_size=100000 of <class 'int'>,
                         map_size=None of <class 'NoneType'>,
                         raised: serial must be 'msgpack' or 'pickle' not something_fancy
        >>> myDB = ShareDB(path='./test_init.ShareDB', reset=True, readers='XYZ', buffer_size=100, map_size=10**3)
        Traceback (most recent call last):
        TypeError: Given path=./test_init.ShareDB/ of <class 'str'>,
                         reset=True of <class 'bool'>,
                         serial=pickle of <class 'str'>,
                         compress=False of <class 'bool'>,
                         readers=XYZ of <class 'str'>,
                         buffer_size=100 of <class 'int'>,
                         map_size=1000 of <class 'int'>,
                         raised: invalid literal for int() with base 10: 'XYZ'
        >>> myDB = ShareDB(path='./test_init.ShareDB', reset=True, readers=40, buffer_size=100, map_size=10**3)
        >>> myDB.path
        './test_init.ShareDB/'
        >>> myDB.is_alive
        True
        >>> myDB.max_readers
        40
        >>> myDB.sync_threshold
        100
        >>> myDB.pending_writes
        0
        >>> myDB.max_map_size
        1000
        >>> len(myDB) == 0
        True
        >>> myDB.drop()
        True
        """
        try:
            # Format path correctly
            path = ShareDB._trim_suffix(given_str=path, suffix="/")
            path = ShareDB._trim_suffix(given_str=path, suffix=".ShareDB")
            path += ".ShareDB/"

            # Reset ShareDB instance if necessary
            if reset:
                ShareDB._clear_path(path)

            # Create path if absent
            if not os.path.isdir(path):
                os.makedirs(path)

            # Determine map_size
            total_disk_space = shutil.disk_usage(path).total
            resolved_map_size = total_disk_space if map_size is None else map_size

            # Create configuration if absent
            if not os.path.exists(path + "ShareDB.config"):
                config = ShareDB._store_config(
                    path,
                    serial,
                    compress,
                    readers,
                    buffer_size,
                    min(resolved_map_size, total_disk_space),
                )
            # Otherwise load configuration
            else:
                config = ShareDB._load_config(path)

            # Setup ShareDB instance
            self.path = path  # Path to ShareDB
            self.is_alive = True  # Instance is alive

            # (Un)serialization scheme argument
            self.serial = config.get("ShareDB Config", "SERIAL")

            # Whether to compress packed values for storage?
            self.compress = config.getboolean("ShareDB Config", "COMPRESS")

            # Serialization function to use for (un)packing keys and values
            self._pack_key, self._unpack_key, self._pack_val, self._unpack_val = ShareDB._get_serial_funcs(
                serial=self.serial, compress=self.compress
            )

            # Number of processes reading in parallel
            self.max_readers = config.getint("ShareDB Config", "READERS")

            # Trigger sync after this many items inserted
            self.sync_threshold = config.getint("ShareDB Config", "BCSIZE")

            # Approx. no. of items to sync in ShareDB
            self.pending_writes = 0

            # Memory map size, maybe larger than RAM
            self.max_map_size = config.getint("ShareDB Config", "MSLIMIT")

            # Instantiate the underlying LMDB structure
            self._db = lmdb.open(
                self.path,
                subdir=True,
                map_size=self.max_map_size,
                create=True,
                readahead=False,
                writemap=True,
                map_async=True,
                max_readers=self.max_readers,
                max_dbs=0,
                lock=True,
            )

        except Exception as exc:
            raise TypeError(
                """Given path={} of {},
                 reset={} of {},
                 serial={} of {},
                 compress={} of {},
                 readers={} of {},
                 buffer_size={} of {},
                 map_size={} of {},
                 raised: {}""".format(
                    path,
                    type(path),
                    reset,
                    type(reset),
                    serial,
                    type(serial),
                    compress,
                    type(compress),
                    readers,
                    type(readers),
                    buffer_size,
                    type(buffer_size),
                    map_size,
                    type(map_size),
                    exc,
                )
            )

    @staticmethod
    def _trim_suffix(given_str, suffix):
        """Remove a trailing suffix from a string if present.

        Parameters
        ----------
        given_str : str
            The string to trim.
        suffix : str
            The suffix to remove if present at the end of given_str.

        Returns
        -------
        str
            given_str without the trailing suffix, or given_str unchanged.
        """
        if given_str.endswith(suffix):
            return given_str[: -len(suffix)]
        return given_str

    @staticmethod
    def _clear_path(path):
        """Delete the file or directory at path.

        Parameters
        ----------
        path : str
            Filesystem path to delete.

        Returns
        -------
        None
        """
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            filepath = path.rstrip("/")
            if os.path.isfile(filepath):
                os.remove(filepath)

    @staticmethod
    def _store_config(path, serial, compress, readers, buffer_size, map_size):
        """Write a new ShareDB configuration file to disk.

        Parameters
        ----------
        path : str
            Directory path where the config file will be written.
        serial : str
            Serialization backend (``'msgpack'`` or ``'pickle'``).
        compress : bool
            Whether values are zlib-compressed.
        readers : int
            Maximum number of concurrent readers.
        buffer_size : int
            Number of inserts before an automatic sync.
        map_size : int
            Maximum byte size allocated for storage.

        Returns
        -------
        configparser.RawConfigParser
            The configuration object that was written to disk.
        """
        config = configparser.RawConfigParser()
        config.add_section("ShareDB Config")
        config.set("ShareDB Config", "SERIAL", str(serial).lower())
        config.set("ShareDB Config", "COMPRESS", str(compress))
        config.set("ShareDB Config", "READERS", str(readers))
        config.set("ShareDB Config", "BCSIZE", str(buffer_size))
        config.set("ShareDB Config", "MSLIMIT", str(map_size))
        config_file_path = path + "ShareDB.config"
        with open(config_file_path, "w") as config_file:
            config.write(config_file)
        return config

    @staticmethod
    def _load_config(path):
        """Read and return the ShareDB configuration file from disk.

        Parameters
        ----------
        path : str
            Directory path containing the config file.

        Returns
        -------
        configparser.RawConfigParser
            The loaded configuration object.
        """
        config = configparser.RawConfigParser()
        config_file_path = path + "ShareDB.config"
        with open(config_file_path) as config_file:
            config.read_file(config_file)
        return config

    @staticmethod
    def _get_base_packer(serial):
        """Return the base serialization function for the given backend.

        Parameters
        ----------
        serial : str
            Serialization backend; ``'msgpack'`` or ``'pickle'``.

        Returns
        -------
        callable
            A function that serializes a Python object to bytes.
        """
        if serial == "msgpack":
            return lambda x: msgpack.packb(x, use_bin_type=True)
        return lambda x: pickle.dumps(x, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def _get_base_unpacker(serial):
        """Return the base deserialization function for the given backend.

        Parameters
        ----------
        serial : str
            Serialization backend; ``'msgpack'`` or ``'pickle'``.

        Returns
        -------
        callable
            A function that deserializes bytes to a Python object.
        """
        if serial == "msgpack":
            return lambda x: msgpack.unpackb(x, raw=False, use_list=True)
        return lambda x: pickle.loads(x)

    @staticmethod
    def _get_compressed_packer(serial):
        """Return a packer that serializes then zlib-compresses its input.

        Parameters
        ----------
        serial : str
            Serialization backend; ``'msgpack'`` or ``'pickle'``.

        Returns
        -------
        callable
            A function that serializes and compresses a Python object to bytes.
        """
        base_packer = ShareDB._get_base_packer(serial)
        return lambda x: zlib.compress(base_packer(x))

    @staticmethod
    def _get_decompressed_unpacker(serial):
        """Return an unpacker that zlib-decompresses then deserializes its input.

        Parameters
        ----------
        serial : str
            Serialization backend; ``'msgpack'`` or ``'pickle'``.

        Returns
        -------
        callable
            A function that decompresses and deserializes bytes to a Python object.
        """
        base_unpacker = ShareDB._get_base_unpacker(serial)
        return lambda x: base_unpacker(zlib.decompress(x))

    @staticmethod
    def _get_serial_funcs(serial, compress):
        """Select and return the four (un)packing callables for a given configuration.

        Parameters
        ----------
        serial : str
            Serialization backend; ``'msgpack'`` or ``'pickle'``.
        compress : bool
            If True, use compressed value packing/unpacking.

        Returns
        -------
        tuple
            A four-tuple (key_packer, key_unpacker, value_packer, value_unpacker)
            of callables.

        Raises
        ------
        ValueError
            If serial is not ``'msgpack'`` or ``'pickle'``.
        """
        # Validate serial argument
        if serial not in ["msgpack", "pickle"]:
            raise ValueError(
                "serial must be 'msgpack' or 'pickle' not {}".format(serial)
            )

        # Setup base (un)packing functions
        base_packer = ShareDB._get_base_packer(serial)
        base_unpacker = ShareDB._get_base_unpacker(serial)

        # Setup key (un)packing functions
        key_packer = base_packer
        key_unpacker = base_unpacker

        # Setup value (un)packing functions
        if compress:
            value_packer = ShareDB._get_compressed_packer(serial)
            value_unpacker = ShareDB._get_decompressed_unpacker(serial)
        else:
            value_packer = base_packer
            value_unpacker = base_unpacker

        # Return all (un)packer methods
        return key_packer, key_unpacker, value_packer, value_unpacker

    def alivemethod(method):
        """Gate a ShareDB method so it raises RuntimeError when the instance is closed or dropped."""

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if self.is_alive:
                return method(self, *args, **kwargs)
            else:
                raise RuntimeError(
                    "Access to {} has been closed or dropped".format(repr(self))
                )

        return wrapper

    def __repr__(self):
        """Return a string representation of the ShareDB instance.

        Returns
        -------
        str
            A human-readable string identifying the ShareDB instance and its path.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_repr.ShareDB', reset=True)
        >>> myDB
        ShareDB instantiated from ./test_repr.ShareDB/
        >>> myDB.drop()
        True
        """
        return "ShareDB instantiated from {}".format(self.path)

    def __str__(self):
        """Return a string representation of the ShareDB instance.

        Returns
        -------
        str
            A human-readable string identifying the ShareDB instance and its path.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_str.ShareDB', reset=True)
        >>> myDB
        ShareDB instantiated from ./test_str.ShareDB/
        >>> myDB.drop()
        True
        """
        return repr(self)

    def _get_packed_key(self, key):
        """Pack a key, raising descriptive errors for invalid inputs.

        Parameters
        ----------
        key : object
            A valid key to serialize.

        Returns
        -------
        bytes
            The serialized key.

        Raises
        ------
        TypeError
            If key is None or cannot be serialized.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_get_packed_key', serial='msgpack', reset=True)
        >>> test_key = [1, '2', 3.0, None]
        >>> myDB._get_packed_key(key=test_key) == msgpack.packb(test_key, use_bin_type=True)
        True
        >>> myDB._get_packed_key(key=set(test_key[:1]))
        Traceback (most recent call last):
        TypeError: Given key={1} of <class 'set'>, raised: can not serialize 'set' object
        >>> myDB._get_packed_key(key=None)
        Traceback (most recent call last):
        TypeError: ShareDB cannot use <class 'NoneType'> objects as keys
        >>> myDB.drop()
        True
        """
        if key is None:
            raise TypeError("ShareDB cannot use {} objects as keys".format(type(None)))
        try:
            key = self._pack_key(key)
        except Exception as exc:
            raise TypeError("Given key={} of {}, raised: {}".format(key, type(key), exc))
        return key

    def _get_unpacked_key(self, key):
        """Deserialize a packed key, raising descriptive errors for invalid inputs.

        Parameters
        ----------
        key : bytes
            A valid serialized key to deserialize.

        Returns
        -------
        object
            The deserialized key.

        Raises
        ------
        TypeError
            If key is None or cannot be deserialized.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_get_unpacked_key.ShareDB', reset=True)
        >>> test_key = [1, '2', 3.0, None]
        >>> myDB._get_unpacked_key(key=myDB._get_packed_key(key=test_key)) == test_key
        True
        >>> myDB.drop()
        True
        """
        if key is None:
            raise TypeError("ShareDB cannot use {} objects as keys".format(type(None)))
        try:
            key = self._unpack_key(key)
        except Exception as exc:
            raise TypeError("Given key={} of {}, raised: {}".format(key, type(key), exc))
        return key

    def _get_packed_val(self, val):
        """Pack a value, raising descriptive errors for invalid inputs.

        Parameters
        ----------
        val : object
            A valid value to serialize.

        Returns
        -------
        bytes
            The serialized value.

        Raises
        ------
        TypeError
            If val is None or cannot be serialized.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_get_packed_val.ShareDB', serial='msgpack', reset=True)
        >>> test_val = {0: [1, '2', 3.0, None]}
        >>> myDB._get_packed_val(val=test_val) == msgpack.packb(test_val, use_bin_type=True)
        True
        >>> myDB._get_packed_val(val=set(test_val[0][:1]))
        Traceback (most recent call last):
        TypeError: Given value={1} of <class 'set'>, raised: can not serialize 'set' object
        >>> myDB._get_packed_val(val=None)
        Traceback (most recent call last):
        TypeError: ShareDB cannot use <class 'NoneType'> objects as values
        >>> myDB.drop()
        True
        """
        if val is None:
            raise TypeError(
                "ShareDB cannot use {} objects as values".format(type(None))
            )
        try:
            val = self._pack_val(val)
        except Exception as exc:
            raise TypeError(
                "Given value={} of {}, raised: {}".format(val, type(val), exc)
            )
        return val

    def _get_unpacked_val(self, val):
        """Deserialize a packed value, raising descriptive errors for invalid inputs.

        Parameters
        ----------
        val : bytes
            A valid serialized value to deserialize.

        Returns
        -------
        object
            The deserialized value.

        Raises
        ------
        TypeError
            If val is None or cannot be deserialized.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_get_unpacked_val.ShareDB', reset=True)
        >>> test_val = {0: [1, '2', 3.0, None]}
        >>> myDB._get_unpacked_val(val=myDB._get_packed_val(val=test_val)) == test_val
        True
        >>> myDB.drop()
        True
        """
        if val is None:
            raise TypeError(
                "ShareDB cannot use {} objects as values".format(type(None))
            )
        try:
            val = self._unpack_val(val)
        except Exception as exc:
            raise TypeError(
                "Given value={} of {}, raised: {}".format(val, type(val), exc)
            )
        return val

    def _trigger_sync(self):
        """Flush to disk if the insert buffer has reached its configured limit."""
        if self.pending_writes >= self.sync_threshold:
            self.sync()
            self.pending_writes = 0
        return None

    def _insert_kv_in_txn(self, key, val, txn):
        """Pack and insert a key-value pair using an existing write transaction.

        Parameters
        ----------
        key : object
            An unpacked key to insert or overwrite.
        val : object
            An unpacked value to associate with key.
        txn : lmdb.Transaction
            An open LMDB write transaction.

        Returns
        -------
        None

        Raises
        ------
        MemoryError
            If the database map is full.
        TypeError
            If key or val cannot be serialized.
        """
        key = self._get_packed_key(key=key)
        val = self._get_packed_val(val=val)
        try:
            txn.put(key=key, value=val, overwrite=True, append=False)
        except lmdb.MapFullError:
            raise MemoryError("{} is full".format(str(self)))
        except Exception as exc:
            raise TypeError(
                "Given key={} of {} and value={} of {} raised: {}".format(
                    key, type(key), val, type(val), exc
                )
            )
        self.pending_writes += 1
        self._trigger_sync()
        return None

    @alivemethod
    def set(self, key, val):
        """Insert or overwrite a single key-value pair.

        Parameters
        ----------
        key : object
            A valid key to insert or update.
        val : object
            A valid value to associate with key.

        Returns
        -------
        ShareDB
            self.

        Raises
        ------
        TypeError
            If key or val cannot be serialized, or if either is None.
        MemoryError
            If the database is full.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_set.ShareDB', serial='msgpack', reset=True)
        >>> myDB.set(key=('NAME'), val='Ayaan Hossain')
        ShareDB instantiated from ./test_set.ShareDB/
        >>> myDB.set(key=['KEY'], val=set(['SOME_VALUE']))
        Traceback (most recent call last):
        TypeError: Given value={'SOME_VALUE'} of <class 'set'>, raised: can not serialize 'set' object
        >>> myDB.set(key=(1, 2, 3, 4), val='SOME_VALUE')
        ShareDB instantiated from ./test_set.ShareDB/
        >>> myDB.set(key='ANOTHER KEY', val=[1, 2, 3, 4])
        ShareDB instantiated from ./test_set.ShareDB/
        >>> myDB.drop()
        True
        """
        with self._db.begin(write=True) as txn:
            self._insert_kv_in_txn(key=key, val=val, txn=txn)
        return self

    def __setitem__(self, key, val):
        """Insert or overwrite a single key-value pair using index notation.

        Parameters
        ----------
        key : object
            A valid key to insert or update.
        val : object
            A valid value to associate with key.

        Returns
        -------
        None

        Raises
        ------
        TypeError
            If key or val cannot be serialized, or if either is None.
        MemoryError
            If the database is full.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_set_dunder.ShareDB', serial='msgpack', reset=True)
        >>> myDB['NAME']  = 'Ayaan Hossain'
        >>> myDB[['KEY']] = 'SOME_VALUE'
        >>> myDB['KEY'] = 'SOME_VALUE'
        >>> myDB['ANOTHER KEY'] = [1, 2, 3, 4]
        >>> myDB[['KEY']] == 'SOME_VALUE'
        True
        >>> myDB[set(['KEY'])] = 'SOME_VALUE'
        Traceback (most recent call last):
        TypeError: Given key={'KEY'} of <class 'set'>, raised: can not serialize 'set' object
        >>> myDB.drop()
        True
        """
        return self.set(key=key, val=val)

    @alivemethod
    def multiset(self, kv_iter):
        """Insert or update multiple key-value pairs in a single transaction.

        Parameters
        ----------
        kv_iter : iterable
            An iterable of (key, value) pairs to insert or update.

        Returns
        -------
        ShareDB
            self.

        Raises
        ------
        Exception
            If any error occurs while iterating over kv_iter.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_multi_set.ShareDB', serial = 'msgpack', reset=True)
        >>> kv_generator = ((tuple(range(i, i+5)), tuple(range(i+5, i+10))) for i in range(10))
        >>> myDB.multiset(kv_iter=kv_generator).sync().length()
        10
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_multi_set.ShareDB', reset=False)
        >>> len(myDB)
        10
        >>> kv_generator = ((tuple(range(i, i+5)), tuple(range(i+5, i+10))) for i in range(3000, 3005))
        >>> myDB.multiset(kv_iter=kv_generator)
        ShareDB instantiated from ./test_multi_set.ShareDB/
        >>> len(myDB)
        15
        >>> for i in range(3005, 3010): myDB[tuple(range(i, i+5))] = tuple(range(i+5, i+10))
        >>> len(myDB)
        20
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_multi_set.ShareDB', reset=False)
        >>> len(myDB)
        20
        >>> myDB[tuple(range(3005, 3010))] == list(range(3010, 3015))
        True
        >>> myDB[tuple(range(1))] = set(range(1))
        Traceback (most recent call last):
        TypeError: Given value={0} of <class 'set'>, raised: can not serialize 'set' object
        >>> myDB[set(range(1))] = range(1)
        Traceback (most recent call last):
        TypeError: Given key={0} of <class 'set'>, raised: can not serialize 'set' object
        >>> myDB.drop()
        True
        """
        with self._db.begin(write=True) as txn:
            try:
                for key, val in kv_iter:
                    self._insert_kv_in_txn(key=key, val=val, txn=txn)
            except Exception as exc:
                raise Exception(
                    "Given kv_iter={} of {}, raised: {}".format(
                        kv_iter, type(kv_iter), exc
                    )
                )
        return self

    @alivemethod
    def update(self, other):
        """Insert or update items from a mapping or iterable of key-value pairs.

        Parameters
        ----------
        other : dict or iterable
            A mapping (dict-like) or iterable of (key, value) pairs to insert.

        Returns
        -------
        ShareDB
            self.

        Raises
        ------
        Exception
            If any error occurs during insertion.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_update.ShareDB', reset=True)
        >>> myDB.update({'a': 1, 'b': 2})
        ShareDB instantiated from ./test_update.ShareDB/
        >>> myDB['a']
        1
        >>> myDB.update((('c', 3), ('d', 4)))
        ShareDB instantiated from ./test_update.ShareDB/
        >>> myDB['d']
        4
        >>> myDB.drop()
        True
        """
        if hasattr(other, "items"):
            return self.multiset(kv_iter=other.items())
        return self.multiset(kv_iter=other)

    def _get_val_on_disk(self, key, txn, key_is_packed=False, default=None):
        """Return the raw (packed) value for a key using an existing transaction.

        Parameters
        ----------
        key : object
            A key to query.
        txn : lmdb.Transaction
            An open LMDB read or write transaction.
        key_is_packed : bool, optional
            If False, pack the key before querying. Default is False.
        default : object, optional
            Value to return when the key is absent. Default is None.

        Returns
        -------
        bytes or object
            The packed bytes value if the key is present, otherwise default.
        """
        if not key_is_packed:
            key = self._get_packed_key(key=key)
        return txn.get(key=key, default=default)

    def _get_unpacked_val_on_disk(self, key, txn, key_is_packed=False, default=None):
        """Return the deserialized value for a key using an existing transaction.

        Parameters
        ----------
        key : object
            A key to query.
        txn : lmdb.Transaction
            An open LMDB read or write transaction.
        key_is_packed : bool, optional
            If False, pack the key before querying. Default is False.
        default : object, optional
            Value to return when the key is absent. Default is None.

        Returns
        -------
        object
            The deserialized value if the key is present, otherwise default.
        """
        val = self._get_val_on_disk(key=key, txn=txn, key_is_packed=key_is_packed, default=default)
        if val is default:
            return default
        return self._get_unpacked_val(val)

    @alivemethod
    def get(self, key, default=None):
        """Query the value associated with a single key.

        Parameters
        ----------
        key : object
            A valid key to query for its associated value.
        default : object, optional
            Value to return when the key is absent. Default is None.

        Returns
        -------
        object
            The deserialized value for key, or default if the key is absent.

        Raises
        ------
        TypeError
            If key is None or cannot be serialized.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_get_dunder.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = i**0.5
        >>> len(myDB)
        100
        >>> myDB.close()
        True
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
        """
        with self._db.begin(write=False) as txn:
            val = self._get_unpacked_val_on_disk(
                key=key, txn=txn, key_is_packed=False, default=default
            )
        return val

    @alivemethod
    def setdefault(self, key, default):
        """Return the value for a key if present, otherwise insert it with a default value.

        Parameters
        ----------
        key : object
            A valid key to query or insert.
        default : object
            The value to insert and return if key is absent.

        Returns
        -------
        object
            The existing value for key if present, otherwise default.

        Raises
        ------
        TypeError
            If key is None or cannot be serialized, or if default is None.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_setdefault.ShareDB', reset=True)
        >>> myDB.setdefault(key='x', default=42)
        42
        >>> myDB.setdefault(key='x', default=99)
        42
        >>> myDB.drop()
        True
        """
        with self._db.begin(write=True) as txn:
            packed_key = self._get_packed_key(key=key)
            raw_val = txn.get(key=packed_key)
            if raw_val is None:
                packed_val = self._get_packed_val(val=default)
                txn.put(key=packed_key, value=packed_val, overwrite=True, append=False)
                self.pending_writes += 1
                self._trigger_sync()
                return default
            return self._get_unpacked_val(val=raw_val)

    def __getitem__(self, key):
        """Query the value associated with a single key using index notation.

        Parameters
        ----------
        key : object
            A valid key to query for its associated value.

        Returns
        -------
        object
            The deserialized value for key.

        Raises
        ------
        KeyError
            If the key is absent.
        TypeError
            If key is None or cannot be serialized.

        Examples
        --------
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
        KeyError: "key=49.0 of <class 'float'> is absent"
        >>> myDB[set([49.0])]
        Traceback (most recent call last):
        KeyError: "key={49.0} of <class 'set'> is absent"
        >>> myDB.drop()
        True
        """
        val = self.get(key=key, default=None)
        if val is None:
            raise KeyError("key={} of {} is absent".format(key, type(key)))
        return val

    @alivemethod
    def multiget(self, key_iter, default=None):
        """Query values for multiple keys in a single transaction.

        Parameters
        ----------
        key_iter : iterable
            An iterable of valid keys to query for values.
        default : object, optional
            Value to yield when a key is absent. Default is None.

        Returns
        -------
        generator
            A generator of deserialized values, or default for absent keys.

        Raises
        ------
        Exception
            If any error occurs while iterating over key_iter.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_multiget.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = i**2
        >>> len(myDB)
        100
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_multiget.ShareDB', reset=False)
        >>> len(list(myDB.multiget(key_iter=range(100), default=None))) == 100
        True
        >>> next(myDB.multiget(key_iter=range(100, 110), default=False))
        False
        >>> next(myDB.multiget(key_iter=[None]))
        Traceback (most recent call last):
        Exception: Given key_iter=[None] of <class 'list'>, raised: ShareDB cannot use <class 'NoneType'> objects as keys
        >>> myDB.drop()
        True
        """
        with self._db.begin(write=False) as txn:
            try:
                for key in key_iter:
                    yield self._get_unpacked_val_on_disk(
                        key=key, txn=txn, key_is_packed=False, default=default
                    )
            except Exception as exc:
                raise Exception(
                    "Given key_iter={} of {}, raised: {}".format(
                        key_iter, type(key_iter), exc
                    )
                )

    @alivemethod
    def has_key(self, key):
        """Check whether a single key exists in the store.

        Parameters
        ----------
        key : object
            A candidate key to check for presence.

        Returns
        -------
        bool
            True if the key is present, False otherwise.

        Raises
        ------
        TypeError
            If key is None or cannot be serialized.

        Examples
        --------
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
        """
        with self._db.begin(write=False) as txn:
            val = self._get_val_on_disk(
                key=key, txn=txn, key_is_packed=False, default=None
            )
        return val is not None

    def __contains__(self, key):
        """Check whether a single key exists in the store using the ``in`` operator.

        Parameters
        ----------
        key : object
            A candidate key to check for presence.

        Returns
        -------
        bool
            True if the key is present, False otherwise.

        Raises
        ------
        TypeError
            If key is None or cannot be serialized.

        Examples
        --------
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
        """
        return self.has_key(key=key)

    @alivemethod
    def has_multikey(self, key_iter):
        """Check existence of multiple keys in a single transaction.

        Parameters
        ----------
        key_iter : iterable
            An iterable of candidate keys to check for presence.

        Returns
        -------
        generator
            A generator of booleans; True for each present key, False otherwise.

        Raises
        ------
        Exception
            If any error occurs while iterating over key_iter.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_has_multikey', reset=True)
        >>> myDB.multiset((i, [i**0.5, i**2.0]) for i in range(100, 200))
        ShareDB instantiated from ./test_has_multikey.ShareDB/
        >>> len(myDB)
        100
        >>> list(myDB.has_multikey(range(100, 105)))
        [True, True, True, True, True]
        >>> list(myDB.clear().has_multikey(range(100, 105)))
        [False, False, False, False, False]
        >>> next(myDB.multiset(((i,[i**0.5, i**2.0]) for i in range(100))).has_multikey([0, 1, 2]))
        True
        >>> myDB.drop()
        True
        """
        with self._db.begin(write=False) as txn:
            try:
                for key in key_iter:
                    val = self._get_val_on_disk(
                        key=key, txn=txn, key_is_packed=False, default=None
                    )
                    yield val is not None
            except Exception as exc:
                raise Exception(
                    "Given key_iter={} of {}, raised: {}".format(
                        key_iter, type(key_iter), exc
                    )
                )

    @alivemethod
    def length(self):
        """Return the number of key-value pairs stored in the instance.

        Returns
        -------
        int
            The count of stored entries.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_length', reset=True, serial='pickle')
        >>> for i in range(500, 600): myDB[i] = set([2.0*i])
        >>> len(myDB)
        100
        >>> myDB.sync().clear().length()
        0
        >>> myDB.drop()
        True
        """
        return int(self._db.stat()["entries"])

    def __len__(self):
        """Return the number of key-value pairs stored in the instance.

        Returns
        -------
        int
            The count of stored entries.

        Examples
        --------
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
        """
        return self.length()

    def _del_pop_from_disk(self, key, txn, operation, key_is_packed=False):
        """Delete or pop a key-value pair using an existing write transaction.

        Parameters
        ----------
        key : object
            A candidate key to remove.
        txn : lmdb.Transaction
            An open LMDB write transaction.
        operation : str
            Operation mode; ``'del'`` to delete without returning the value,
            or ``'pop'`` to delete and return the value.
        key_is_packed : bool, optional
            If False, pack the key before operating. Default is False.

        Returns
        -------
        object or None
            The deserialized value if operation is ``'pop'``, otherwise None.

        Raises
        ------
        KeyError
            If operation is ``'pop'`` and the key is absent.
        ValueError
            If operation is not ``'del'`` or ``'pop'``.
        """
        if not key_is_packed:
            key = self._get_packed_key(key=key)
        if operation == "del":
            deleted = txn.delete(key=key)
            val = None
            if not deleted:
                return val
        elif operation == "pop":
            raw_val = txn.pop(key=key)
            if raw_val is None:
                key = self._get_unpacked_key(key=key)
                raise KeyError("key={} of {} is absent".format(key, type(key)))
            val = self._get_unpacked_val(val=raw_val)
        else:
            raise ValueError("operation must be 'del' or 'pop' not {}".format(operation))
        self.pending_writes += 1
        self._trigger_sync()
        return val

    @alivemethod
    def remove(self, key):
        """Remove a single key from the store.

        Parameters
        ----------
        key : object
            A candidate key to remove.

        Returns
        -------
        ShareDB
            self.

        Raises
        ------
        TypeError
            If key is None or cannot be serialized.

        Examples
        --------
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
        """
        with self._db.begin(write=True) as txn:
            self._del_pop_from_disk(key=key, txn=txn, operation="del", key_is_packed=False)
        return self

    def __delitem__(self, key):
        """Remove a single key from the store using ``del`` notation.

        Parameters
        ----------
        key : object
            A candidate key to remove.

        Returns
        -------
        None

        Raises
        ------
        TypeError
            If key is None or cannot be serialized.

        Examples
        --------
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
        """
        return self.remove(key=key)

    @alivemethod
    def multiremove(self, key_iter):
        """Remove multiple keys in a single transaction.

        Parameters
        ----------
        key_iter : iterable
            An iterable of candidate keys to remove.

        Returns
        -------
        ShareDB
            self.

        Raises
        ------
        Exception
            If any error occurs while iterating over key_iter.

        Examples
        --------
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
        """
        with self._db.begin(write=True) as txn:
            try:
                for key in key_iter:
                    self._del_pop_from_disk(
                        key=key, txn=txn, operation="del", key_is_packed=False
                    )
            except Exception as exc:
                raise Exception(
                    "Given key_iter={} of {}, raised: {}".format(
                        key_iter, type(key_iter), exc
                    )
                )
        return self

    @alivemethod
    def pop(self, key, default=_SENTINEL):
        """Remove and return the value for a single key.

        Parameters
        ----------
        key : object
            A valid key to pop from the store.
        default : object, optional
            Value to return if the key is absent. If omitted, a KeyError
            is raised for absent keys. Default is <absent>.

        Returns
        -------
        object
            The deserialized value that was stored under key, or default.

        Raises
        ------
        KeyError
            If the key is absent and no default was supplied.
        TypeError
            If key is None or cannot be serialized.

        Examples
        --------
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
        KeyError: "key=49 of <class 'int'> is absent"
        >>> myDB.pop(49, 'missing')
        'missing'
        >>> myDB.drop()
        True
        """
        try:
            with self._db.begin(write=True) as txn:
                val = self._del_pop_from_disk(
                    key=key, txn=txn, operation="pop", key_is_packed=False
                )
            return val
        except KeyError:
            if default is not ShareDB._SENTINEL:
                return default
            raise

    @alivemethod
    def multipop(self, key_iter):
        """Remove and yield values for multiple keys in a single transaction.

        Parameters
        ----------
        key_iter : iterable
            An iterable of valid keys to pop from the store.

        Returns
        -------
        generator
            A generator of deserialized values for each popped key.

        Raises
        ------
        Exception
            If any error occurs while iterating over key_iter, including absent keys.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_multipop.ShareDB', reset=True)
        >>> for i in range(100): myDB[i] = [i**0.5]
        >>> len(myDB)
        100
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_multipop', reset=False)
        >>> pop_iter = myDB.multipop(range(49, 74))
        >>> next(pop_iter)
        [7.0]
        >>> len(list(pop_iter))
        24
        >>> len(myDB)
        75
        >>> pop_iter = myDB.multipop([199, 200])
        >>> next(pop_iter)
        Traceback (most recent call last):
        Exception: Given key_iter=[199, 200] of <class 'list'>, raised: "key=199 of <class 'int'> is absent"
        >>> myDB.drop()
        True
        """
        with self._db.begin(write=True) as txn:
            try:
                for key in key_iter:
                    yield self._del_pop_from_disk(
                        key=key, txn=txn, operation="pop", key_is_packed=False
                    )
            except Exception as exc:
                raise Exception(
                    "Given key_iter={} of {}, raised: {}".format(
                        key_iter, type(key_iter), exc
                    )
                )

    def _iter_on_disk_kv(
        self, yield_key=False, unpack_key=False, yield_val=False, unpack_val=False
    ):
        """Stream key and/or value data from the underlying LMDB store.

        Parameters
        ----------
        yield_key : bool
            If True, include keys in the output.
        unpack_key : bool
            If True, deserialize keys before yielding.
        yield_val : bool
            If True, include values in the output.
        unpack_val : bool
            If True, deserialize values before yielding.

        Returns
        -------
        generator
            A generator of (un)packed keys, values, or (key, value) pairs.

        Examples
        --------
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
        """
        if not any([yield_key, yield_val]):
            raise ValueError(
                "Both yield_key and yield_val to ._iter_on_disk_kv() are False or None"
            )
        with self._db.begin(write=False) as txn:
            with txn.cursor() as cursor:
                for key, val in cursor:
                    # Unpack key
                    if unpack_key:
                        key = self._get_unpacked_key(key=key)
                    # Unpack value
                    if unpack_val:
                        val = self._get_unpacked_val(val=val)
                    # Stream keys and values
                    if yield_key and not yield_val:
                        yield key
                    elif yield_val and not yield_key:
                        yield val
                    elif yield_key and yield_val:
                        yield key, val

    @alivemethod
    def items(self):
        """Iterate over all key-value pairs in the store.

        Returns
        -------
        generator
            A generator of deserialized (key, value) pairs.

        Examples
        --------
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
        """
        return self._iter_on_disk_kv(
            yield_key=True, unpack_key=True, yield_val=True, unpack_val=True
        )

    @alivemethod
    def keys(self):
        """Iterate over all keys in the store.

        Returns
        -------
        generator
            A generator of deserialized keys.

        Examples
        --------
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
        """
        return self._iter_on_disk_kv(yield_key=True, unpack_key=True)

    @alivemethod
    def __iter__(self):
        """Iterate over all keys in the store.

        Returns
        -------
        generator
            A generator of deserialized keys.

        Examples
        --------
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
        """
        return self.keys()

    @alivemethod
    def values(self):
        """Iterate over all values in the store.

        Returns
        -------
        generator
            A generator of deserialized values.

        Examples
        --------
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
        """
        return self._iter_on_disk_kv(yield_val=True, unpack_val=True)

    @alivemethod
    def popitem(self):
        """Remove and return one key-value pair from the store.

        Returns
        -------
        tuple
            A (key, value) pair deserialized from storage.

        Raises
        ------
        KeyError
            If the store is empty.

        Examples
        --------
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
        """
        packed_key_iter = self._iter_on_disk_kv(yield_key=True, unpack_key=False)
        try:
            packed_key = next(packed_key_iter)
        except StopIteration:
            raise KeyError("popitem(): ShareDB is empty")
        with self._db.begin(write=True) as txn:
            key, val = (
                self._get_unpacked_key(key=packed_key),
                self._del_pop_from_disk(
                    key=packed_key, txn=txn, operation="pop", key_is_packed=True
                ),
            )
        return key, val

    @alivemethod
    def multipopitem(self, num_items=1):
        """Remove and yield multiple key-value pairs in a single transaction.

        Parameters
        ----------
        num_items : int or float, optional
            Maximum number of items to pop. Capped at the current store size.
            Default is 1.

        Returns
        -------
        generator
            A generator of up to num_items deserialized (key, value) pairs.

        Raises
        ------
        TypeError
            If num_items is not a numeric type.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_multipopitem.ShareDB', reset=True)
        >>> myDB.multiset((i,i**2) for i in range(10)).length()
        10
        >>> len(list(myDB.keys()))
        10
        >>> myDB.close()
        True
        >>> myDB = ShareDB(path='./test_multipopitem', reset=False)
        >>> len(list(myDB.multipopitem(num_items='THIS IS NOT A NUMBER')))
        Traceback (most recent call last):
        TypeError: num_items=THIS IS NOT A NUMBER of <class 'str'> must be an integer/long/float
        >>> len(list(myDB.multipopitem(num_items=len(myDB)*1.0)))
        10
        >>> 1 in myDB
        False
        >>> len(list(myDB.multiset((i,i**2) for i in range(10)).multipopitem(num_items=15)))
        10
        >>> myDB.drop()
        True
        """
        # Check if num_items is valid, and set up accordingly
        if not isinstance(num_items, numbers.Real):
            raise TypeError(
                "num_items={} of {} must be an integer/long/float".format(
                    num_items, type(num_items)
                )
            )

        # Iterate over ShareDB and load num_item keys in packed state
        num_items = min(num_items, self.length())  # safe upper limit
        packed_key_iter = self._iter_on_disk_kv(yield_key=True, unpack_key=False)
        packed_keys = []
        while len(packed_keys) < num_items:
            packed_keys.append(next(packed_key_iter))

        # Pop packed keys in packed_keys, and yield the unapacked items
        with self._db.begin(write=True) as txn:
            for packed_key in packed_keys:
                yield (
                    self._get_unpacked_key(key=packed_key),
                    self._del_pop_from_disk(
                        key=packed_key, txn=txn, operation="pop", key_is_packed=True
                    ),
                )

    @alivemethod
    def sync(self):
        """Flush all pending writes to disk.

        Returns
        -------
        ShareDB
            self.
        """
        self._db.sync()
        return self

    def _delete_keys_and_db(self, delete_db):
        """Clear all entries from the LMDB database, optionally deleting it.

        Parameters
        ----------
        delete_db : bool
            If True, delete the named database; if False, only clear its entries.

        Returns
        -------
        None
        """
        with self._db.begin(write=True) as txn:
            named_db = self._db.open_db()
            txn.drop(db=named_db, delete=delete_db)

    @alivemethod
    def clear(self):
        """Remove all key-value pairs from the store.

        Returns
        -------
        ShareDB
            self.

        Examples
        --------
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
        """
        self._delete_keys_and_db(delete_db=False)
        self.pending_writes = 0
        return self

    def close(self):
        """Sync and close the store, marking the instance as inactive.

        Returns
        -------
        bool
            True if the instance was open and has been closed, False if already closed.

        Examples
        --------
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
        >>> myDB.is_alive
        False
        >>> 1 in myDB
        Traceback (most recent call last):
        RuntimeError: Access to ShareDB instantiated from ./test_close.ShareDB/ has been closed or dropped
        >>> myDB = ShareDB(path='./test_close.ShareDB', reset=False)
        >>> myDB.drop()
        True
        """
        if self.is_alive:
            self.sync()
            self._db.close()
            self.is_alive = False
            return True
        return False

    def drop(self):
        """Delete all data and remove the store directory from disk.

        Returns
        -------
        bool
            True if the instance was open and has been dropped, False if already closed.

        Examples
        --------
        >>> myDB = ShareDB(path='./test_drop.ShareDB', reset=True)
        >>> for i in range(10): myDB[list(range(i, i+5))] = list(range(i+5, i+10))
        >>> len(myDB)
        10
        >>> len(myDB)
        10
        >>> myDB.drop()
        True
        >>> myDB.is_alive
        False
        >>> 0 in myDB
        Traceback (most recent call last):
        RuntimeError: Access to ShareDB instantiated from ./test_drop.ShareDB/ has been closed or dropped
        >>> myDB = ShareDB(path='./test_drop.ShareDB', reset=False)
        >>> len(myDB)
        0
        >>> myDB.drop()
        True
        """
        if self.is_alive:
            self._delete_keys_and_db(delete_db=True)
            self.close()
            self._clear_path(self.path)
            return True
        return False


def main():
    """Run the module's embedded doctests."""
    import doctest

    doctest.testmod()


if __name__ == "__main__":
    main()
