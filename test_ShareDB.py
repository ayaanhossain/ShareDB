from ShareDB import ShareDB

import random
import pytest


def test_ShareDB_instantiation_fails():
    '''
    Test Exceptions be raised on bad instantiation.
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

@pytest.fixture
def msgpack_myDB():
    '''
    Initialize a test.ShareDB with msgpack serialization.
    '''
    return ShareDB(path='./myDB.msgpack',
        reset=True,
        serial='msgpack',
        readers=40,
        buffer_size=100,
        map_size=10**5)

@pytest.fixture
def pickle_myDB():
    '''
    Initialize a test.ShareDB with msgpack serialization.
    '''
    return ShareDB(path='./myDB.pickle',
        reset=True,
        serial='pickle',
        readers=40,
        buffer_size=100,
        map_size=10**5)

def test_ShareDB_instantiation_success(msgpack_myDB, pickle_myDB):
    '''
    Test instance variables on successful instantiation.
    '''
    assert msgpack_myDB.PATH     == './myDB.msgpack.ShareDB/'
    assert pickle_myDB.PATH      == './myDB.pickle.ShareDB/'
    assert msgpack_myDB.ALIVE    == pickle_myDB.ALIVE    == True
    assert msgpack_myDB.PARALLEL == pickle_myDB.PARALLEL == 40
    assert msgpack_myDB.BCSIZE   == pickle_myDB.BCSIZE   == 100
    assert msgpack_myDB.BQSIZE   == pickle_myDB.BQSIZE   == 0
    assert msgpack_myDB.MSLIMIT  == pickle_myDB.MSLIMIT  == 100000

def test_set_and_get(msgpack_myDB, pickle_myDB):
    '''
    Test set/__setitem__, get/__getitem__ and related Exceptions.
    '''
    # Successful sets
    msgpack_myDB.set(key='Name', val='Ayaan Hossain').\
                 set(key=(1, 2, 3, 4), val=['SOME', 'VALUES', 'HERE'])
    pickle_myDB['Name']       = 'Ayaan Hossain'
    pickle_myDB[(1, 2, 3, 4)] = ['SOME', 'VALUES', 'HERE']
    pickle_myDB[set(['pickle', 'can', 'store', 'sets'])] = True

    # Sets that raise Exception
    with pytest.raises(TypeError) as error:
        msgpack_myDB.set(key=set(['msgpack', 'can', 'store', 'sets']), val=False)
    with pytest.raises(TypeError) as error:
        msgpack_myDB.set('None cannot be values', None)
    with pytest.raises(TypeError) as error:
        msgpack_myDB.set(None, 'None cannot be keys')
    with pytest.raises(TypeError) as error:
        pickle_myDB.set('None cannot be values', None)
    with pytest.raises(TypeError) as error:
        pickle_myDB.set(None, 'None cannot be keys')

    # Successful gets
    assert msgpack_myDB['Name']          == 'Ayaan Hossain'
    assert msgpack_myDB[(1, 2, 3, 4)]    == ['SOME', 'VALUES', 'HERE']
    assert pickle_myDB.get('Name')       == 'Ayaan Hossain'
    assert pickle_myDB.get((1, 2, 3, 4)) == ['SOME', 'VALUES', 'HERE']
    assert pickle_myDB[set(['pickle', 'can', 'store', 'sets'])] == True

    # Gets that raise Exception
    with pytest.raises(TypeError) as error:
        msgpack_myDB.get(key=None)
    with pytest.raises(TypeError) as error:
        pickle_myDB[None]


def test_multiset_and_multiget(msgpack_myDB, pickle_myDB):
    pass

if __name__ == '__main__':
    pass