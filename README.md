# ShareDB
ShareDB is a lightweight on-disk key-value store with a  dictionary-like interface built on top of LMDB and is intended to replace a python dictionary when:

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