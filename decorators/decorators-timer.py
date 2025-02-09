#!/usr/bin/env python3

# build-in modules
import random
import time
from functools import wraps


def set_timer(func):
    """
    A decorator to measure the execution time of a function.

    This decorator wraps the given function and prints the execution time to the console
    when the function is called.

    Args:
        func (callable): The function to be timed.

    Returns:
        callable: The wrapped function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        Wrapper function to measure the execution time of the decorated function.

        It records the time before and after the function execution and prints the difference.

        Args:
            *args: Positional arguments passed to the decorated function.
            **kwargs: Keyword arguments passed to the decorated function.

        Returns:
            The result of the decorated function.
        """
        start_time = time.monotonic()  # Record the start time
        result = func(*args, **kwargs)  # Execute the original function
        end_time = time.monotonic()  # Record the end time
        execution_time = end_time - start_time  # Calculate the execution time
        print(
            f"The function {func.__name__} took {execution_time:.4f} seconds to execute."
        )  # Print the execution time
        return result  # Return the result of the original function

    return wrapper


@set_timer
def example(value: float) -> None:
    """
    An example function that simulates a task taking some time to execute.

    This function simply sleeps for a specified number of seconds.

    Args:
        value (float): The amount of time to sleep in seconds.
    Returns:
        None
    """
    time.sleep(value)  # Simulate work by sleeping


if __name__ == "__main__":
    random_sleep_time = random.uniform(1, 5)  # Generate a random float between 1 and 5

    print("Running the example function...")
    example(random_sleep_time)  # Call the example function with the random sleep time
    print("Example finished.")
