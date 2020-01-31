from ShareDB         import ShareDB
from multiprocessing import Process, Pool, cpu_count

import numpy as np
import time


def execute_task(args):
    return execute_actual_task(*args)

def execute_actual_task(inputDB_path, process_id, processes):
    inputDB  = ShareDB(inputDB_path)

    outputDB = ShareDB(
        path='./task_distribution/solution_{}'.format(process_id),
        reset=True,
        serial='msgpack',
        compress=True,
        map_size=10**8)

    current_token  = process_id
    task_end_token = 'END_{}'.format(process_id)

    wait_printed = False
    while True:
        if current_token not in inputDB:
            if task_end_token not in inputDB:
                if not wait_printed:
                    print 'WAITING WORK # {}'.format(current_token)
                    wait_printed = True
                continue
            else:
                wait_printed = False
                print 'PROCESS COMPLETED # {}'.format(process_id)
                break
        else:
            print 'EXECUTING WORK # {}'.format(current_token)
            X, Y = inputDB[current_token]
            result = list(np.convolve(X, Y))
            outputDB[current_token] = result
            print 'COMPLETED WORK # {}'.format(current_token)
            current_token += processes

    outputDB.close()

def init_task(inputDB, max_tasks, processes):
    i = 0
    time.sleep(1)
    while i < max_tasks:
        token = i
        base_size = np.random.randint(10000, 100000)
        X = list(np.random.randint(10, size=(1, base_size))[0])
        Y = list(np.random.randint(10, size=(1, base_size))[0])
        inputDB[token] = [X, Y]
        print 'QUEUED WORK # {}'.format(i)
        i += 1
        # time.sleep(0.01)

    i = 0
    while i < processes:
        inputDB['END_{}'.format(i)] = True
        print 'QUEUED ENDT # {}'.format(i)
        i += 1

def serial_version():
    inputDB = ShareDB(
        path='./task_distribution/input',
        reset=True,
        serial='msgpack',
        compress=True,
        map_size=10**8)

    max_tasks = 100
    process_id = 0

    t0 = time.time()

    total_processes = 1

    np.random.seed(20)

    init_task(inputDB, max_tasks=max_tasks, processes=total_processes)

    execute_task((inputDB.PATH, process_id, total_processes))

    print 'Total time elapsed = {} seconds'.format(time.time() - t0)

def process_version():
    inputDB = ShareDB(
        path='./task_distribution/input',
        reset=True,
        serial='msgpack',
        compress=False,
        map_size=10**8)

    max_tasks = 100
    process_id = 0

    t0 = time.time()

    total_processes = cpu_count() - 1

    # np.random.seed(20)

    init_process = Process(
        target=init_task, args=(inputDB, max_tasks, total_processes,))
    init_process.start()

    task_processes = []
    while process_id < total_processes:
        task_process = Process(
            target=execute_actual_task, args=(
                inputDB.PATH, process_id, total_processes))
        task_processes.append(task_process)
        task_process.start()
        process_id += 1

    init_process.join()
    init_process.terminate()
    for process in task_processes:
        process.join()

    inputDB.close()

    print 'Total time elapsed = {} seconds'.format(time.time() - t0)



def main():
    # serial_version()
    process_version()
    # inputDB = ShareDB(
    #     path='./task_distribution/input',
    #     reset=True,
    #     serial='msgpack',
    #     compress=False,
    #     map_size=10**9)

    # max_tasks       = 100
    # process_id      = 0

    # # t0 = time.time()

    # # total_processes = 1

    # # init_task(inputDB, max_tasks=max_tasks, processes=total_processes)

    # # execute_task(inputDB, process_id=process_id, processes=total_processes)

    # # print 'Total time elapsed = {} seconds'.format(time.time() - t0)

    # t0 = time.time()

    # total_processes = cpu_count() - 2
    # init_process = Process(
    #     target=init_task, args=(inputDB, max_tasks, total_processes,))
    # init_process.start()

    # worker_pool = Pool(total_processes)
    # worker_map  = worker_pool.map(execute_task, [
    #     (inputDB.PATH, process_id, total_processes) for process_id in range(
    #         total_processes)])

    # init_process.join()
    # init_process.terminate()
    # inputDB.close()

    # for worker_result in worker_map:
    #     process_id, outputDB_path = worker_result
    #     outputDB = ShareDB(outputDB_path)
    #     print 'Process {} finished with {} results.'.format(
    #         process_id, len(outputDB))
    #     outputDB.drop()
    # inputDB.drop()
    # worker_pool.close()

    # # task_processes = []
    # # while process_id < total_processes:
    # #     task_process = Process(
    # #         target=execute_task, args=(inputDB, process_id, total_processes))
    # #     task_processes.append(task_process)
    # #     process_id += 1

    # # init_process.start()
    # # for process in task_processes:
    # #     process.start()

    # # init_process.join()
    # # for process in task_processes:
    # #     process.join()
    
    # print 'Total time elapsed = {} seconds'.format(time.time() - t0)

if __name__ == '__main__':
    main()
