from ShareDB import ShareDB

import random
import string
import pytest


def test_ShareDB_init_fails_and_drop_success():
    '''
    Test Exceptions be raised on bad instantiation,
    test success of dropping ShareDB once instantiated.
    '''
    with pytest.raises(TypeError) as error:
        myDB = ShareDB()
    with pytest.raises(TypeError) as error:
        myDB = ShareDB(path=True)
    with pytest.raises(TypeError) as error:
        myDB = ShareDB(path=123)
    with pytest.raises(TypeError) as error:
        myDB = ShareDB(
            path='./test_init.ShareDB',
            reset=True,
            serial='something_fancy')
    with pytest.raises(TypeError) as error:
        myDB = ShareDB(
            path='./test_init.ShareDB',
            reset=True,
            readers='XYZ',
            buffer_size=100,
            map_size=10**3)
    myDB = ShareDB(path='./test_init.ShareDB', reset=True)
    assert myDB.drop()

@pytest.fixture
def msgpack_myDB():
    '''
    Initialize a ShareDB with msgpack serialization.
    '''
    msgpack_myDB = ShareDB(path='./myDB.msgpack',
        reset=True,
        serial='msgpack',
        readers=40,
        buffer_size=100,
        map_size=10**7)
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
        readers=40,
        buffer_size=100,
        map_size=10**7)
    yield pickle_myDB
    pickle_myDB.drop()

def test_ShareDB_init_success(msgpack_myDB, pickle_myDB):
    '''
    Test instance variables on successful instantiation.
    '''
    assert msgpack_myDB.PATH     == './myDB.msgpack.ShareDB/'
    assert pickle_myDB.PATH      == './myDB.pickle.ShareDB/'
    assert msgpack_myDB.ALIVE    == pickle_myDB.ALIVE    == True
    assert msgpack_myDB.PARALLEL == pickle_myDB.PARALLEL == 40
    assert msgpack_myDB.BCSIZE   == pickle_myDB.BCSIZE   == 100
    assert msgpack_myDB.BQSIZE   == pickle_myDB.BQSIZE   == 0
    assert msgpack_myDB.MSLIMIT  == pickle_myDB.MSLIMIT  == 10000000

def gri(seed):
    '''
    Helper generator to stream random items.
    '''
    random.seed(seed)
    chars = list(string.ascii_lowercase)
    while True:
        choice = random.randint(0, 10)
        if choice < 5:
            # A random string is generated
            length = random.randint(5, 10)
            result = ''.join(random.choice(chars) for _ in range(length))
        else:
            # A random number is generated
            result = float('{:.6f}'.format(random.random()))
        yield result

@pytest.mark.parametrize('total', [100, 500, 1000, 5000, 10000])
def test_set_and_get(msgpack_myDB, pickle_myDB, total):
    '''
    Test set/__setitem__, get/__getitem__ and related Exceptions.
    '''
    # Successful known sets
    msgpack_myDB.set(key='Name', val='Ayaan Hossain').\
                 set(key=(1, 2, 3, 4), val=['SOME', 'VALUES', 'HERE'])
    pickle_myDB['Name']       = 'Ayaan Hossain'
    pickle_myDB[(1, 2, 3, 4)] = ['SOME', 'VALUES', 'HERE']
    pickle_myDB[set(['pickle', 'can', 'store', 'sets'])] = True

    # Setup random
    seed = random.random()
    gri_stream = gri(seed=seed)

    # Successful random sets
    verification = {}
    while len(verification) < total:
        msg_key = gri_stream.next()
        msg_val = gri_stream.next()
        pkl_key = gri_stream.next()
        pkl_val = gri_stream.next()
        if msg_key in verification:
            verification.pop(msg_key)
        elif pkl_key in verification:
            verification.pop(pkl_key)
        else:
            msgpack_myDB.set(key=msg_key, val=msg_val)
            verification[msg_key] = msg_val        
            pickle_myDB[pkl_key]  = pkl_val
            verification[pkl_key] = pkl_val

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

    # Reset random
    gri_stream = gri(seed=seed)
    new_path = gri_stream.next()

    # Successful random gets
    for _ in range(total):
        msg_key = gri_stream.next()
        msg_val = gri_stream.next()
        pkl_key = gri_stream.next()
        pkl_val = gri_stream.next()
        if (msg_key in verification) and (pkl_key in verification):
            assert msgpack_myDB[msg_key]        == verification[msg_key] == msg_val
            assert pickle_myDB.get(key=pkl_key) == verification[pkl_key] == pkl_val

    # gets that raise Exception
    with pytest.raises(KeyError) as error:
        msgpack_myDB['non-existent key']
    with pytest.raises(TypeError) as error:
        msgpack_myDB.get(key=None)
    with pytest.raises(TypeError) as error:
        pickle_myDB[None]

@pytest.mark.parametrize('total', [100, 500, 1000, 5000, 10000])
def test_multiset_and_multiget(msgpack_myDB, pickle_myDB, total):
    '''
    Test multiset and multiget and related Exceptions.
    '''
    # Setup random
    seed = random.random()
    gri_stream = gri(seed=seed)

    # define factor
    factor = total // 10

    # Successful random multisets
    msgpack_myDB.multiset(kv_iter=(
        ((i, [gri_stream.next(), gri_stream.next(), gri_stream.next()]) \
            for i in range(total))))
    pickle_myDB.multiset(kv_iter=(
        ((i, set([gri_stream.next(), gri_stream.next(), gri_stream.next()])) \
            for i in range(total))))

    # multisets that raise Exception
    with pytest.raises(Exception) as error:
        msgpack_myDB.multiset(kv_iter=(
            ((i, set([gri_stream.next(), gri_stream.next(), gri_stream.next()])) \
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
            gen_val = [gri_stream.next(), gri_stream.next(), gri_stream.next()]
            assert get_vals[idx] == gen_val

    # multigets that raise Exception
    with pytest.raises(Exception) as error:
        msgpack_myDB.multiget(kv_iter=(
            ((i, [None, None, None]) for i in range(total))))
    with pytest.raises(Exception) as error:
        pickle_myDB.multiget(kv_iter=(
            ((None, [i, i, i]) for i in range(total))))


if __name__ == '__main__':
    pass