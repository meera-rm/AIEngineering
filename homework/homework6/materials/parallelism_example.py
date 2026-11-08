from concurrent.futures import ThreadPoolExecutor
from time import perf_counter, sleep


def first_task():
    sleep(2)  # Simulate waiting for work to finish.
    return "First task finished"


def second_task():
    sleep(3)
    return "Second task finished"


def main():
    started = perf_counter()

    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both tasks before waiting, so their waits overlap.
        first_future = executor.submit(first_task)
        second_future = executor.submit(second_task)

        # result() waits for the task and raises any exception it encountered.
        first_result = first_future.result()
        second_result = second_future.result()

    print(first_result)
    print(second_result)
    # About 3 seconds, rather than the 5 seconds needed to run sequentially.
    print(f"Elapsed: {perf_counter() - started:.2f} seconds")


if __name__ == "__main__":
    main()
