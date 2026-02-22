from ShareDB import ShareDB

import time

REPORT_INTERVAL = 0.1  # seconds between progress updates


def write_thp(store_path, num_items, length):
    """
    Fill store with num_items entries and report write throughput.
    """
    kvStore = ShareDB(store_path, True, "msgpack", map_size=num_items * 100)
    t_start = time.time()
    t_report = t_start
    for i in range(1, num_items + 1):
        kvStore[i] = 1
        t = time.time()
        if t - t_report >= REPORT_INTERVAL or i == num_items:
            t_report = t
            print(
                "WRITER thp @ {:,.0f} wt/sec | FILL {:.1f}%".format(
                    i / (t - t_start), 100.0 * i / num_items
                ),
                end="\r",
                flush=True,
            )
    print()


def read_thp(store_path):
    """
    Go through store and report reading throughput.
    """
    kvStore = ShareDB(store_path)
    total = len(kvStore)
    t_start = time.time()
    t_report = t_start
    for i in range(1, total + 1):
        kvStore[i]
        t = time.time()
        if t - t_report >= REPORT_INTERVAL or i == total:
            t_report = t
            print(
                "READER thp @ {:,.0f} rd/sec | SCAN {:.1f}%".format(
                    i / (t - t_start), 100.0 * i / total
                ),
                end="\r",
                flush=True,
            )
    print()


def main():
    store_path = "./kvStore"
    num_items = 1000000
    length = 25
    write_thp(store_path, num_items, length)
    read_thp(store_path)
    ShareDB(store_path).drop()


if __name__ == "__main__":
    main()
