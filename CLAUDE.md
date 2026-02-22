# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -vv

# Run a single test
pytest tests/test_ShareDB.py::test_basic_set_and_get -vv

# Run tests with coverage (matches CI)
pytest -vv --cov=./ --cov-report=xml
```

## Architecture

ShareDB is a Python key-value store with a dict-like interface, backed by [LMDB](http://www.lmdb.tech/doc/) (Lightning Memory-Mapped Database). It is designed for persisting data locally and sharing it across processes.

**Single source file:** All logic lives in `ShareDB/ShareDB.py`. The `ShareDB/__init__.py` simply re-exports the `ShareDB` class.

### Core design

- **Single writer, multiple readers** — concurrent reads are safe; concurrent writes are not.
- **Serialization** — keys and values are serialized to bytes before LMDB storage. Two modes: `msgpack` or `pickle` (default), set at construction and persisted in a config file at `{path}/ShareDB.config`.
- **Optional zlib compression** for values, also persisted in the config.
- **`@alivemethod` decorator** — gates every public method so operations on a closed/dropped database raise an error rather than silently failing. Check `is_alive` attribute to verify state.
- **Auto-sync** — after `buffer_size` (default 100,000) inserts, `sync()` is called automatically to flush to disk.

### Key classes and methods

The `ShareDB` class exposes a dict-like API:
- Single ops: `set`/`get`/`remove`/`pop` (and `__setitem__`/`__getitem__`/`__delitem__`)
- Batch ops: `multiset`, `multiget`, `multiremove`, `multipop`, `multipopitem`
- Iteration: `keys()`, `values()`, `items()`, `__iter__`
- Management: `sync()`, `close()`, `drop()`, `clear()`

Internal helpers follow a `_get_*_packer/unpacker` pattern to select the serializer, and `_insert_kv_in_txn()` handles LMDB transaction batching.

### Tests

Tests use `pytest` with two fixtures (`msgpack_myDB`, `pickle_myDB`) covering both serialization modes. Many tests are parametrized with random data for robustness. The test file is `tests/test_ShareDB.py`.
