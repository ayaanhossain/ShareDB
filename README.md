```
![ShareDB](./logo.png)
```
ShareDB is a lightweight on-disk key-value store with a dictionary-like interface built on top of LMDB and is intended to replace the built-in python dictionary when

 1. the data to store needs to persist on disk for later reuse,
 2. the data needs to be read across multiple processes with minimal overhead, and 
 3. the keys and values can be (de)serialized via msgpack or cPickle.

ShareDB operates via an LMDB structure in an optimistic manner for reading and writing data. As long as you maintain a one-writer-many-reader workflow everything should be fine. Sending a ShareDB instance from parent to children processes is fine, or you may open the same ShareDB in children processes for reading. Parallel writes made in children processes are not safe; they are not guaranteed to be written, and may corrupt instance.

A sample use case

### Table of Contents
-------------------------------
 * [ShareDB in Action](#sharedb-in-action)
 * [Requirements](#requirements)
 * [Installation](#installation)
 * [License and Contribution](#license-and-contribution)
 * [API Reference](#api-reference)

### ShareDB in Action

### Requirements

### Installation

### License and Contribution

### API Reference

