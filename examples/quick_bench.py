import random
import time
import multiprocessing

from ShareDB import ShareDB

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
            print 'WRITER - throughput @ {} writes/second | Filled {}'.format(i / total_time, len(dictionary))
    return population

def worker_process(path, population, pid):
    print 'ENTERED PID {} .. will PROCESS {} items'.format(pid, len(population))
    dictionary = ShareDB(path='./test.ShareDB', reset=False)
    # dictionary = LevelDict(path='./test.ShareDB')
    t0 = time.time()
    total_time = 0.
    # random.shuffle(population)
    for i, item in enumerate(population):
        t0 = time.time()
        # assert item in dictionary
        val = dictionary[item]
        # assert isinstance(val, int)
        # assert val == 0
        # dictionary[item] = val + 1
        # dictionary.sync()

        # assert dictionary[item] == val+1
        total_time += time.time() - t0
        if random.random() < 0.001:
            print 'READER {} - throughput @ {} queries/second | Remaining {}'.format(pid, i / total_time, len(dictionary) - i - 1)
            # time.sleep(0.01)

def main():
    # vedis.Vedis('./test.ShareDB')
    dictionary = ShareDB(path='./test.ShareDB', reset=True)
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
        worker = multiprocessing.Process(
            target=worker_process, args=('./test.ShareDB', population, pid, ))
        workers.append(worker)
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    print '\n READ FINISHED \n'

    dictionary = ShareDB(path='./test.ShareDB', reset=False)
    dictionary.drop()

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

if __name__ == '__main__':
    main()