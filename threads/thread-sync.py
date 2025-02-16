#!/usr/bin/env python3

import logging
import signal
import sys
import threading
import time
from functools import partial
from typing import Dict
import pandas as pd
import uuid

# Initialize logger configuration
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s [%(levelname)s]: %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
THREADS_QTY: int = 99
STATE_CHANGE_DELAY: float = 0.5

# Value definitions
ON = True
OFF = False


class AppControlFlags:
    """
    This class provides flags for controlling application behavior, such as whether to keep running,
    wait between operations, and tracking operational counters. It facilitates monitoring system usage through a counter mechanism.

    Attributes:
        keep_running (bool): Flag indicating if the application should continue executing.
        wait (bool): Flag determining operation timing intervals.
        __WORK_COUNTER (Dict[str, int]): Dictionary tracking counts of various operations.

    Methods:
        add_counter(name: str) -> None:
            Initializes or increments an existing counter for a specified operation. Starts at 0 when first called.
            The same value can be accessed and updated elsewhere in the system with minimal overhead.

        get_counter(name: str) -> int:
            Retrieves the current count of a specific operation. Useful for monitoring usage metrics across the system.

        increment_counter(name: str) -> None:
            Increases the count associated with an operation by 1, providing accurate tracking of activity levels.

        min_counter() -> str:
            Determines which operation has been performed the least number of times according to the counter values.
            Returns the first occurring operation in case of a tie.

        get_all_values() -> Dict[str, int]:
            Returns a dictionary containing all tracked operation counters for program-wide analysis or reporting.
    """

    def __init__(self) -> None:
        self.keep_running = True
        self.wait = True
        self.__WORK_COUNTER: Dict[str, int] = {}

    @property
    def keep_running(self) -> bool:
        """Indicates if the application should continue running."""
        return self._keep_running

    @keep_running.setter
    def keep_running(self, value: bool) -> None:
        """Enforces a change to whether the application will run in the background."""
        self._keep_running = value

    @property
    def wait(self) -> bool:
        """Controls how often operations are performed; true by default means no waiting required."""
        return self._wait

    @wait.setter
    def wait(self, value: bool) -> None:
        """Conditions whether additional delay between operations is necessary."""
        self._wait = value

    def add_counter(self, name: str) -> None:
        """
        Initializes a counter for tracking an operation.

        Args:
            name (str): Name of the operation to track.
        """
        self.__WORK_COUNTER[name] = 0

    def get_counter(self, name: str) -> int:
        """
        Retrieves the current count associated with a specified operation.

        Args:
            name (str): Name of the tracked operation.

        Returns:
            int: Current counter value for the operation.
        """
        return self.__WORK_COUNTER.get(name, 0)

    def increment_counter(self, name: str) -> None:
        """
        Increments the count associated with an operation by one.

        Args:
            name (str): Name of the operation to update.
        """
        if name in self.__WORK_COUNTER:
            self.__WORK_COUNTER[name] += 1

    def min_counter(self) -> str:
        """
        Returns the operation name with the smallest counter value. Ties are resolved by returning the first
        occurrence as stored in the counter dictionary.

        Returns:
            str: Name of the operation with the minimal count.
        """
        return min(self.__WORK_COUNTER.keys(), key=lambda k: self.__WORK_COUNTER[k])

    def get_all_values(self) -> Dict[str, int]:
        """
        Provides a comprehensive view of all tracked operation counters.

        Returns:
            dict: Mapping from operation names to their respective counter values.
        """
        return self.__WORK_COUNTER.copy()


class Job(threading.Thread):
    """
    Executes recurring tasks in a separate thread with synchronized control and prioritization.

    Provides coordinated task execution with thread-safe state management,
    priority-based scheduling, and graceful shutdown capabilities.

    Attributes:
        control (AppControlFlags): Shared application control flags for system state.
        lock (threading.Lock): Coordination lock for thread-safe operations.
        condition (threading.Condition): Synchronization primitive for wait/notify.
        active (bool): Indication about what is the Thread state.Defaults to OFF.
        thread_name (str): Unique identifier for this job instance.
    """

    def __init__(
        self,
        control: AppControlFlags,
        lock: threading.Lock,
        condition: threading.Condition,
        thread_name: str,
    ) -> None:
        """
        Initialize a managed job thread.

        Args:
            control: Shared application state controller
            lock: Mutual exclusion lock for resource protection
            condition: Coordination primitive for thread scheduling
            active: Hold the thread state (ON or OFF)
            thread_name: Unique identifier for this job
        """
        threading.Thread.__init__(self)
        self.name = thread_name

        self._control: AppControlFlags = control
        self._lock: threading.Lock = lock
        self._condition: threading.Condition = condition
        self._active: bool = OFF  # Initial activity state
        self._control.add_counter(name=self.name)
        self.start()

    def __app_is_running(self) -> bool:
        """
        Check if the application is running.

        Returns:
            bool: True if the application should continue running, False otherwise.
        """
        with self._lock:
            return self._control.keep_running

    def __waiting(self) -> None:
        """
        Pause the thread until it is notified to proceed.

        The thread waits on a condition until it is its turn to proceed based on priority.
        """
        with self._condition:
            while True:
                # Check if the thread has the priority to proceed
                got_priority = self.name == self._control.min_counter()

                if not self._control.wait and got_priority:
                    # If the global wait flag is cleared and this thread has priority, exit loop
                    break

                if not got_priority:
                    logger.debug(f"[{self.name}] Waiting for priority...")
                else:
                    logger.debug(
                        f"[{self.name}] Waiting for global wait flag to be cleared..."
                    )

                # Wait for a notification
                self._condition.wait()

            # Once the thread has priority, update the state
            logger.debug(f"[{self.name}] Good to go!")
            self._control.increment_counter(name=self.name)
            self._control.wait = True  # Re-enable the global wait flag

    def __release_wait_flag(self) -> None:
        """
        Release the wait flag and notify all waiting threads.
        """
        with self._condition:
            logger.debug(f"[{self.name}] Releasing wait flag...")
            self._control.wait = False
            self._condition.notify_all()
        logger.debug(
            f"[{self.name}] Toggled {self._control.get_counter(self.name)} times."
        )

    def run(self) -> None:
        """
        Main execution loop managing task lifecycle and coordination.

        Implements priority-based task scheduling with configurable delays
        and system state monitoring for graceful termination.
        """
        logger.info(f"Initializing job thread '{self.name}'")

        try:
            while self.__app_is_running():
                # Wait for the thread's turn to proceed
                self.__waiting()

                # Core task execution block
                self._active = not self._active
                logger.debug(f"{self.name}] Task state update: {self._active}")

                # Stop the thread for a while before changing its state
                # time.sleep(STATE_CHANGE_DELAY)

                # Release the wait flag and notify other threads
                self.__release_wait_flag()

                # Stop the thread for a while after changed its the State
                time.sleep(STATE_CHANGE_DELAY)

            logger.info(f"Job '{self.name}' completed successfully")

        except Exception as e:
            logger.error(f"Task failure in '{self.name}': {e}", exc_info=False)


def handle_sigint(
    app_control_flags: AppControlFlags, lock_flag: threading.Lock, sig: int, frame
) -> None:
    """
    Handle SIGINT (Ctrl+C) signal for graceful shutdown.

    Args:
        app_control_flags (AppControlFlags): Control flags for application state.
        lock_flag (threading.Lock): Synchronization lock.
        sig (int): Received signal number.
        frame (FrameType): Current stack frame.
    """
    logger.info("Ctrl+C detected, shutting down...")
    with lock_flag:
        app_control_flags.keep_running = False


if __name__ == "__main__":
    # Register the signal handler for Ctrl+C (SIGINT)
    logger.info("Starting the application!")

    try:
        # General Application control flags
        app_control_flags = AppControlFlags()

        # Define a lock for synchronization
        lock_flag: threading.Lock = threading.Lock()
        condition_flag: threading.Condition = threading.Condition(lock=lock_flag)

        # Create a partial function to handle SIGINT with control_flags and lock_flag
        sigint_handler = partial(handle_sigint, app_control_flags, lock_flag)
        signal.signal(signal.SIGINT, sigint_handler)

        # Stores Job thread objects and later joins them.
        # Its purpose is to track active threads.
        threads = []

        for i in range(THREADS_QTY):
            t = Job(
                control=app_control_flags,
                lock=lock_flag,
                condition=condition_flag,
                thread_name=str(uuid.uuid4().hex),
            )

            threads.append(t)

        # Signalize the threads after they are all ready to start working
        time.sleep(1)
        with condition_flag:
            app_control_flags.wait = False
            condition_flag.notify_all()

        # Keep the main thread running until the application is stopped
        while app_control_flags.keep_running:
            pass

        logger.info("Releasing resources ...")

        # Wait for all threads to finish
        for t in threads:
            t.join()

        # Fetch the results
        data = app_control_flags.get_all_values()
        # Convert the dictionary to a Pandas DataFrame
        df = pd.DataFrame.from_dict(data, orient="index", columns=["Values"])
        # Reset index to create a new column 'UUID' from the index
        df.reset_index(inplace=True)
        # Rename the 'index' column to 'UUID'
        df.rename(columns={"index": "UUID"}, inplace=True)
        # Log the DataFrame
        logger.info(f"\n\n{df}\n")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

    finally:
        sys.exit(0)
