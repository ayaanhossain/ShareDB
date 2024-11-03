from ShareDB import ShareDB

import random
import string
import pytest


def test_ShareDB_init_param_fails():
    '''
    Test Exceptions to be raised on bad instantiation.
    '''
    with pytest.raises(TypeError) as error:
        myDB = ShareDB()
        myDB.drop()
    with pytest.raises(TypeError) as error:
        myDB = ShareDB(path=True)
        myDB.drop()
    with pytest.raises(TypeError) as error:
        myDB = ShareDB(path=123)
        myDB.drop()
    with pytest.raises(TypeError) as error:
        myDB = ShareDB(
            path='./test_init.ShareDB',
            reset=True,
            serial='something_fancy')
    with pytest.raises(TypeError) as error:
        myDB = ShareDB(
            path='./test_init.ShareDB',
            reset=True,
            serial='pickle',
            compress='AbsoluteTruth')
    with pytest.raises(TypeError) as error:
        myDB = ShareDB(
            path='./test_init.ShareDB',
            reset=True,
            readers='XYZ',
            buffer_size=100,
            map_size=10**3)
    with pytest.raises(TypeError) as error:
        myDB = ShareDB(
            path='./test_init.ShareDB',
            reset=True,
            readers='XYZ',
            buffer_size=100,
            map_size=0)
    myDB = ShareDB(path='./test_init.ShareDB', reset=True)
    myDB.drop()

def test_ShareDB_path():
    '''
    Test Exceptions and success when path is occupied by file.
    '''
    # Setup ShareDB init fail via file occupancy
    path = './test_init.ShareDB'
    with open(path, 'w') as outfile:
        pass

    # Raises TypeError because path points to a file
    with pytest.raises(TypeError) as error:
        myDB = ShareDB(path=path)

    # Automatically remove file when reset is True
    myDB = ShareDB(path=path, reset=True)
    myDB.drop()

def test_close_drop():
    '''
    Test close and drop.
    '''
    # Successful close
    myDB = ShareDB(path='./test_close_drop')
    assert myDB.close() == True
    assert myDB.close() == False

    # Once closed transaction raises RuntimeError
    with pytest.raises(RuntimeError) as error:
        myDB[1] = 2

    # Successful drop
    myDB = ShareDB(path='./test_close_drop', reset=True)
    assert myDB.drop()  == True
    assert myDB.drop()  == False

    # Once dropped transaction raises RuntimeError
    with pytest.raises(RuntimeError) as error:
        myDB[1] = 2

@pytest.fixture
def msgpack_myDB():
    '''
    Initialize a ShareDB with msgpack serialization.
    '''
    msgpack_myDB = ShareDB(path='./myDB.msgpack',
        reset=True,
        serial='msgpack',
        compress=True,
        readers=40,
        buffer_size=100,
        map_size=10**7)
    msgpack_myDB = None
    msgpack_myDB = ShareDB(path='./myDB.msgpack',
        reset=False)
    yield msgpack_myDB
    msgpack_myDB.drop()

@pytest.fixture
def pickle_myDB():
    '''
    Initialize a ShareDB with pickle serialization.
    '''
    pickle_myDB = ShareDB(path='./myDB.pickle',
        reset=True,
        serial='pickle',
        compress=True,
        readers=40,
        buffer_size=100,
        map_size=10**7)
    pickle_myDB = None
    pickle_myDB = ShareDB(path='./myDB.pickle',
        reset=False)
    yield pickle_myDB
    pickle_myDB.drop()

def test_ShareDB_init_success(msgpack_myDB, pickle_myDB):
    '''
    Test instance variables on successful instantiation.
    '''
    assert msgpack_myDB.PATH     == './myDB.msgpack.ShareDB/'
    assert pickle_myDB.PATH      == './myDB.pickle.ShareDB/'
    assert msgpack_myDB.ALIVE    == pickle_myDB.ALIVE    == True
    assert msgpack_myDB.SERIAL   == 'msgpack'
    assert pickle_myDB.SERIAL    == 'pickle'
    assert msgpack_myDB.COMPRESS == pickle_myDB.COMPRESS == True
    assert msgpack_myDB.READERS  == pickle_myDB.READERS  == 40
    assert msgpack_myDB.BCSIZE   == pickle_myDB.BCSIZE   == 100
    assert msgpack_myDB.BQSIZE   == pickle_myDB.BQSIZE   == 0
    assert msgpack_myDB.MSLIMIT  == pickle_myDB.MSLIMIT  == 10000000
    assert repr(msgpack_myDB)    == 'ShareDB instantiated from ./myDB.msgpack.ShareDB/'
    assert str(pickle_myDB)      == 'ShareDB instantiated from ./myDB.pickle.ShareDB/'

def test_basic_set_and_get(msgpack_myDB, pickle_myDB):
    '''
    Test basic set/__setitem__, get/__getitem__ and related Exceptions.
    '''
    # Successful known sets
    msgpack_myDB.set(key='Name', val='Ayaan Hossain').\
                 set(key=(1, 2, 3, 4), val=['SOME', 'VALUES', 'HERE'])
    pickle_myDB['Name']       = 'Ayaan Hossain'
    pickle_myDB[(1, 2, 3, 4)] = ['SOME', 'VALUES', 'HERE']
    pickle_myDB[set(['pickle', 'can', 'store', 'sets'])] = True

    # sets that raise Exception
    with pytest.raises(TypeError) as error:
        msgpack_myDB.set(
            key=set(['msgpack', 'can', 'store', 'sets']),
            val=False)
    with pytest.raises(TypeError) as error:
        msgpack_myDB.set('None cannot be values', None)
    with pytest.raises(TypeError) as error:
        msgpack_myDB.set(None, 'None cannot be keys')
    with pytest.raises(TypeError) as error:
        pickle_myDB.set('None cannot be values', None)
    with pytest.raises(TypeError) as error:
        pickle_myDB.set(None, 'None cannot be keys')

    # Successful gets
    assert msgpack_myDB.get('non-existent key') is None
    assert msgpack_myDB['Name']          == 'Ayaan Hossain'
    assert msgpack_myDB[(1, 2, 3, 4)]    == ['SOME', 'VALUES', 'HERE']
    assert pickle_myDB.get('Name')       == 'Ayaan Hossain'
    assert pickle_myDB.get((1, 2, 3, 4)) == ['SOME', 'VALUES', 'HERE']
    assert pickle_myDB[set(['pickle', 'can', 'store', 'sets'])] == True

    # gets that raise Exception
    with pytest.raises(KeyError) as error:
        msgpack_myDB['non-existent key']
    with pytest.raises(TypeError) as error:
        msgpack_myDB.get(key=None)
    with pytest.raises(TypeError) as error:
        pickle_myDB[None]

def gri(seed):
    '''
    Helper generator to stream random items.
    '''
    random.seed(seed)
    chars = list(string.ascii_lowercase)
    while True:
        choice = random.randint(1, 10)
        if choice <= 5:
            # A random string is generated
            length = random.randint(5, 10)
            val = ''.join(random.choice(chars) for _ in range(length))
        else:
            # A random number is generated
            val = float('{:.6f}'.format(random.random()))
        if choice <= 5:
            # tuple result
            result = (val)
        else:
            # unpacked result
            result = val
        yield result

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_set_and_get(msgpack_myDB, pickle_myDB, total):
    '''
    Test random set/__setitem__, get/__getitem__.
    '''
    # Setup random
    seed = random.random()
    gri_stream = gri(seed=seed)

    # Successful random sets
    verification = {}
    while len(verification) < total:
        key = next(gri_stream)
        val = next(gri_stream)
        if key not in verification:
            msgpack_myDB.set(key=key, val=val)
            pickle_myDB[key]  = val
            verification[key] = val

    # Successful random gets
    for key in verification:
        assert msgpack_myDB[key]        == verification[key]
        assert pickle_myDB.get(key=key) == verification[key]

@pytest.mark.parametrize('total', [random.randint(10**2, 10**3)*10 for _ in range(5)])
def test_random_multiset_and_multiget(msgpack_myDB, pickle_myDB, total):
    '''
    Test random multiset and multiget and related Exceptions.
    '''
    # Setup random
    seed = random.random()
    gri_stream = gri(seed=seed)

    # define factor
    factor = total // 10

    # Successful random multisets
    msgpack_myDB.multiset(kv_iter=(
        ((i, [next(gri_stream), next(gri_stream), next(gri_stream)]) \
            for i in range(total))))
    pickle_myDB.multiset(kv_iter=(
        ((i, set([next(gri_stream), next(gri_stream), next(gri_stream)])) \
            for i in range(total))))

    # multisets that raise Exception
    with pytest.raises(Exception) as error:
        msgpack_myDB.multiset(kv_iter=(
            ((i, set([next(gri_stream), next(gri_stream), next(gri_stream)])) \
                for i in range(total))))
    with pytest.raises(Exception) as error:
        pickle_myDB.multiset(kv_iter=(
            ((i, None) for i in range(total))))

    # Reset random
    gri_stream = gri(seed=seed)

    # Successful random multigets
    for i in range(0, total, factor):
        get_vals = list(msgpack_myDB.multiget(key_iter=list(range(i, i+factor))))
        gen_vals = []
        for idx,j in enumerate(range(i, i+factor)):
            gen_val = [next(gri_stream), next(gri_stream), next(gri_stream)]
            assert get_vals[idx] == gen_val

    # multigets that raise Exception
    with pytest.raises(Exception) as error:
        next(msgpack_myDB.multiget(key_iter=[None for _ in range(total)]))
    with pytest.raises(Exception) as error:
        next(pickle_myDB.multiget(key_iter=(None for _ in range(total))))

def get_tinyDB(map_size):
    '''
    Initialize a ShareDB with msgpack serialization.
    '''
    myDB = ShareDB(path='./tinyDB',
        reset=True,
        serial='msgpack',
        readers=40,
        buffer_size=100,
        map_size=map_size)
    return myDB

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_memory_fail(total):
    '''
    Test random MemoryError when ShareDB is imporperly instantiated.
    '''
    # Setup DB and random
    myDB = get_tinyDB(map_size=total//100)
    seed = random.random()
    gri_stream = gri(seed=seed)

    # sets that raise MemoryError
    with pytest.raises(MemoryError):
        for _ in range(total):
            myDB.set(key=next(gri_stream), val=next(gri_stream))

    # Clear myDB
    myDB.drop()

def get_myDB_resources(total):
    '''
    Initialize a populated ShareDB instance and associated resources.
    '''
    # Setup random
    seed = random.random()
    gri_stream = gri(seed=seed)

    # Initialize ShareDB instance
    myDB = ShareDB(path='./myDB',
        reset=True,
        serial=random.choice(['msgpack', 'pickle']),
        compress=random.choice([True, False]),
        readers=40,
        buffer_size=100,
        map_size=10**7)

    # Populate myDB with random items and record keys
    key_val_dict = {}
    while len(key_val_dict) < total:
        key = next(gri_stream)
        val = next(gri_stream)
        if key not in key_val_dict:
            myDB[key] = val
            key_val_dict[key] = val

    # Generate some keys not seen before
    non_key_set = set()
    while len(non_key_set) < total:
        non_key = next(gri_stream)
        if non_key not in key_val_dict:
            non_key_set.add(non_key)

    # Return resources
    return myDB, key_val_dict, non_key_set

def clean_myDB_resources(myDB):
    '''Drop DB.'''
    myDB.drop()

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_contains_has_multikey(total):
    '''
    Test random has_key/__contains__/has_multikey.
    '''
    # Buid and unpack myDB and other resources
    myDB, key_val_dict, non_key_set = get_myDB_resources(total)

    # Successful random __contains__
    for key in key_val_dict:
        assert key in myDB
    for non_key in non_key_set:
        assert myDB.has_key(non_key) == False

    # Successful random has_multikey
    assert all(myDB.has_multikey(key_val_dict.keys())) == True
    assert not all(myDB.has_multikey(non_key_set))   == True

    # Clear resources
    clean_myDB_resources(myDB)

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_lengths(total):
    '''
    Test random length/__len__.
    '''
    db_length = random.randint(total//10, total*10)

    # Successful random length
    myDB, _, __ = get_myDB_resources(db_length)
    assert len(myDB) == db_length

    clean_myDB_resources(myDB)

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_remove(total):
    '''
    Test random remove and related Exception.
    '''
    myDB, key_val_dict, non_key_set = get_myDB_resources(total)

    # Successful random remove
    for key in key_val_dict:
        del myDB[key]
        assert key not in myDB
    for key in non_key_set:
        del myDB[key]

    # remove that raises Exception
    with pytest.raises(TypeError) as _:
        myDB.remove(None)

    clean_myDB_resources(myDB)

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_multiremove(total):
    '''
    Test random multiremove and related Exception.
    '''
    myDB, key_val_dict, non_key_set = get_myDB_resources(total)

    # Successful random multiremove
    while len(myDB):
        factor   = random.randint(0, len(myDB))
        prev_len = len(myDB)
        myDB.multiremove(key_iter=(key_val_dict.popitem()[0] for _ in range(factor)))
        assert len(myDB) == prev_len - factor
    myDB.multiremove(non_key_set)

    # multiremove that raises Exception
    with pytest.raises(Exception) as _:
        myDB.multiremove([None]*factor)

    clean_myDB_resources(myDB)

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_pop(total):
    '''
    Test random pop and related Exceptions.
    '''
    myDB, key_val_dict, non_key_set = get_myDB_resources(total)

    # Successful random pop
    for key in key_val_dict:
        val = myDB.pop(key)
        assert key not in myDB
        assert key_val_dict[key] == val

    # pops that raise KeyError
    for key in key_val_dict:
        with pytest.raises(KeyError) as _:
            myDB.pop(key)
    for non_key in non_key_set:
        with pytest.raises(KeyError) as _:
            myDB.pop(non_key)

    clean_myDB_resources(myDB)

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_multipop(total):
    '''
    Test random multipop.
    '''
    myDB, key_val_dict, non_key_set = get_myDB_resources(total)

    # Successful random multipop
    while len(key_val_dict):
        factor   = random.randint(0, len(myDB))
        prev_len = len(myDB)
        keys_to_pop = list(key_val_dict.keys())[:factor]
        popped_vals = list(myDB.multipop(key_iter=keys_to_pop))
        assert len(myDB) == prev_len - factor
        assert [key_val_dict[key] for key in keys_to_pop] == popped_vals
        for key in keys_to_pop:
            key_val_dict.pop(key)

    # multipop that raises Exception
    with pytest.raises(Exception) as _:
        next(myDB.multipop(key_iter=non_key_set))

    clean_myDB_resources(myDB)

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_items(total):
    '''
    Test random items.
    '''
    myDB, key_val_dict, _ = get_myDB_resources(total)
    myDB_items   = set(myDB.items())
    mydict_items = set(key_val_dict.items())
    assert myDB_items == mydict_items
    clean_myDB_resources(myDB)

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_keys(total):
    '''
    Test random keys.
    '''
    myDB, key_val_dict, _ = get_myDB_resources(total)
    myDB_keys   = set(myDB.keys())
    mydict_keys = set(key_val_dict.keys())
    assert myDB_keys == mydict_keys
    clean_myDB_resources(myDB)

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_iters(total):
    '''
    Test random iters.
    '''
    myDB, key_val_dict, _ = get_myDB_resources(total)
    selected_keys = list(key_val_dict.keys())[:random.randint(0, total//10)]
    for key in selected_keys:
        assert key in list(iter(myDB))
    clean_myDB_resources(myDB)

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_values(total):
    '''
    Test random values.
    '''
    myDB, key_val_dict, _ = get_myDB_resources(total)
    myDB_vals   = set(myDB.values())
    mydict_vals = set(key_val_dict.values())
    assert myDB_vals == mydict_vals
    clean_myDB_resources(myDB)

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_popitem(total):
    '''
    Test random popitem.
    '''
    myDB, key_val_dict, _ = get_myDB_resources(total)
    while key_val_dict:
        popped_key, popped_val = myDB.popitem()
        assert key_val_dict[popped_key] == popped_val
        key_val_dict.pop(popped_key)
    clean_myDB_resources(myDB)

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_multipopitem(total):
    '''
    Test random multipopitem.
    '''
    myDB, key_val_dict, _ = get_myDB_resources(total)
    while len(myDB):
        num_items = random.randint(0, len(myDB)*2)
        prev_len  = len(myDB)
        popped_items = myDB.multipopitem(num_items=num_items)
        for popped_key,popped_val in popped_items:
            assert key_val_dict[popped_key] == popped_val
        assert len(myDB) == max(0, prev_len - num_items)

    # multiremove that raises Exception
    with pytest.raises(Exception) as error:
        myDB.multiremove([None]*factor)

    clean_myDB_resources(myDB)

@pytest.mark.parametrize('total', [random.randint(10**3, 10**4) for _ in range(5)])
def test_random_clear(total):
    '''
    Test random clear.
    '''
    myDB, _, __ = get_myDB_resources(total)
    myDB.clear()
    assert len(myDB) == 0
    clean_myDB_resources(myDB)

if __name__ == '__main__':
    pass