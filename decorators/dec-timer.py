#!/usr/bin/env python3

# build-in modules
import time
import random


def set_timer(func):
    """
    A decorator to measure the execution time of a function.
    
    Args:
        func (callable): The function to be timed.
    
    Returns:
        callable: The wrapped function.
    """

    def wrapper(*args, **kwargs):
        """
        Wrapper function to measure the execution time of the decorated function.

        Args:
            *args: Positional arguments passed to the decorated function.
            **kwargs: Keyword arguments passed to the decorated function.

        Returns:
            The result of the decorated function.
        """
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        time_passed = end - start
        print(f"The function {func.__name__} took {time_passed} seconds.")
        return result
    return wrapper


@set_timer
def example(value) -> None:
    """
    An example function that simulates a task taking some time to execute.

    Args:
        value (float): The amount of time to sleep in seconds.
    """

    time.sleep(value)


if __name__ == '__main__':

    rnd = random.randint(1, 5)

    print('Running the functions ...')
    example(rnd)
