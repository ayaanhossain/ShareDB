from ShareDB import ShareDB

import time


def write_thp(store_path, num_items, length):
    '''
    Fill store with random DNA strings and report throughput.
    '''
    kvStore = ShareDB(
        store_path,
        True,
        'msgpack', 
        map_size=num_items*100)
    i  = 1.
    tt = 0.0
    while i <= num_items:
        t0  = time.time()
        kvStore[i] = 1
        tt += time.time() - t0
        print('WRITER thp @ {:.2f} wt/sec | FILL {:.2f}%'.format(
            i / tt, (100. * i) / num_items))
        i += 1

def read_thp(store_path):
    '''
    Go through store and report reading throughput.
    '''
    kvStore = ShareDB(store_path)
    i  = 1.
    tt = 0.0
    while i <= len(kvStore):
        t0  = time.time()
        val = kvStore[i]
        tt += time.time() - t0
        print('READER thp @ {:.2f} rd/sec | SCAN {:.2f}%'.format(
            i / tt, (100. * i) / len(kvStore)))
        i += 1

def main():
    store_path = './kvStore'
    num_items  = 1000000
    length     = 25
    write_thp(store_path, num_items, length)
    print('\n')
    read_thp(store_path)
    ShareDB(store_path).drop()


if __name__ == '__main__':
    main()