from ShareDB         import ShareDB
from multiprocessing import Process, cpu_count
from itertools       import chain

import numpy as np
import time
import shutil


'''
This example shows the use of ShareDB in parallel computing of linear
discrete convolution of vector pairs.

The vectors generated are rather large, so all data is stored and
distributed via SharedDB instances. This makes all available memory
free for computing the actual result. Additionally, all values are
stored in compressed format, further minimizing disk space.
'''


def stream_tasks(inDB_path, num_task, num_proc):
    '''
    This procedure generates all vector pairs and stores them
    in a ShareDB instance located at inDB_path. Once all the
    work is queued up, the task end tokens are issued.
    '''
    # Open inDB to write vector pairs
    inDB = ShareDB(
        path=inDB_path,     # Store output where specified
        reset=True,         # Recreate inDB if previously existing
        serial='msgpack',   # msgpack offers optimal serialization for lists
        readers=num_proc+1, # Allow all (num_proc) processes to read in parallel
        compress=True,      # Serialized msgpack-ed lists are further compressed
        map_size=5*10**8)     # And we estimate to require ~500MB for results

    # Queue all work
    current_token = 0
    while current_token < num_task:
        # Choose vector size
        base_size = np.random.randint(10**4, 10**5)
        
        # Generate vectors
        X = list(np.random.randint(100, size=(1, base_size))[0])
        Y = list(np.random.randint(100, size=(1, base_size))[0])
        
        # Write to inDB
        inDB[current_token] = [X, Y]
        
        print('QUEUED WORK # {}'.format(current_token))
        
        current_token += 1 # Jump to next token

    # Close inDB
    inDB.close()

def stream_task_token(exec_id, num_task, num_proc):
    '''
    Helper function, simulates range(start, stop, incr).
    '''
    i = exec_id
    while i < num_task:
        yield i
        i += num_proc

def para_conv(inDB_path, outDB_path, exec_id, num_task, num_proc):
    '''
    This procedure computes the convolution of vector pairs stored in a
    ShareDB instance located at inDB_path, and writes the results in a
    ShareDB instance located in outDB_path. The procedure ends when
    no more tasks are available and a relevant task end token is found.
    '''
    # Open inDB to read vector pairs
    inDB = ShareDB(path=inDB_path)

    # Open outDB to write convolution results
    outDB = ShareDB(
        path=outDB_path,    # Store output where specified
        reset=True,         # Recreate outDB if previously existing
        serial='msgpack',   # msgpack offers optimal serialization for lists
        readers=num_proc+1, # At most 2 processes would read outDB in parallel
        compress=True,      # Serialized msgpack-ed lists are further compressed
        map_size=5*10**8 // num_proc) # And we split total allocation uniformly

    # Actual computation loop
    key_iter = stream_task_token(exec_id, num_task, num_proc)
    current_token = exec_id
    # Get vector pairs
    for X, Y in inDB.multiget(key_iter):
        # Log execution initation
        print('EXECUTING WORK # {}'.format(current_token))

        # Actual execution
        result = list(np.convolve(X, Y)) # Compute and store result in a list
        outDB[current_token] = result    # Insert compressed result in outDB
        
        # Log execution computation
        print('COMPLETED WORK # {}'.format(current_token))

        # Update token for logging
        current_token += num_proc

    # Log executor completion
    print('EXECUTOR # {} COMPLETED'.format(exec_id))

    # Time to close outDB ... we're done!
    outDB.close()

def merge_results(mergeDB_path, outDB_paths):
    '''
    This procedure simply merges all individual outDBs into a single
    ShareDB instance stored at mergeDB_path.
    '''
    # Open mergeDB to store merged convolution results
    mergeDB = ShareDB(
        path=mergeDB_path,  # Store output where specified
        reset=True,         # Recreate outDB if previously existing
        serial='msgpack',   # msgpack offers optimal serialization for lists
        readers=2,          # At most 2 processes would read outDB in parallel
        compress=True,      # Serialized msgpack-ed lists are further compressed
        map_size=5*10**8)     # And we estimate to require ~500MB for results

    # # Open and chain all key-value pairs in results
    # outDB_list = (ShareDB(path) for path in outDB_paths)
    # results    = chain.from_iterable(
    #     outDB.items() for outDB in outDB_list)

    # # Merge all individual results
    # mergeDB.multiset(results)

    # # All results merged ... we're done!
    # mergeDB.close()

    # Merge all individual results
    for outDB_path in outDB_paths:
        outDB = ShareDB(outDB_path)
        mergeDB.multiset(outDB.items())
        print('Merged results = {}'.format(len(mergeDB)))

    # All results merged ... we're done!
    mergeDB.close()

def main():
    # Setup variables
    inDB_path = './task_DBs/in.ShareDB'
    num_task  = 100
    num_proc  = cpu_count()

    
    # Log streaming starting time
    t0 = time.time()

    # Fire task streamer
    task_streamer = Process(
        target=stream_tasks, args=(inDB_path, num_task, num_proc))
    task_streamer.start()

    # Join streamer process
    task_streamer.join()

    # Log elapsed time
    print('\nTask Streaming = {} seconds\n'.format(time.time()-t0))

    
    # Log execution starting time
    t0 = time.time()

    # Fire task executors
    task_executors = []
    outDB_paths    = []
    for exec_id in range(num_proc):
        outDB_path = './task_DBs/out{}.ShareDB'.format(exec_id)
        outDB_paths.append(outDB_path)
        task_executor = Process(
            target=para_conv, args=(
                inDB_path, outDB_path, exec_id, num_task, num_proc))
        task_executors.append(task_executor)
        task_executor.start()

    # Join all executor processes
    for task_executor in task_executors:
        task_executor.join()

    # Log elapsed time
    print('\nTask Execution = {} seconds\n'.format(time.time()-t0))

    
    # Log execution starting time
    t0 = time.time()

    # Merge all results
    mergeDB_path = './task_DBs/results.ShareDB'
    merge_results(mergeDB_path, outDB_paths)

    # Cleanup all stores
    shutil.rmtree('task_DBs')

    # Log elapsed time
    print('\nResult Merging = {} seconds\n'.format(time.time()-t0))


if __name__ == '__main__':
    main()