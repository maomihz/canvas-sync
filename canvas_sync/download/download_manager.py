from canvas_sync import log

from threading import Lock, Event
from queue import Queue

from math import ceil

from concurrent.futures import ThreadPoolExecutor
from . import DownloadTask


class DownloadManager:
    """Maintains a list of download tasks and run them concurrently."""
    def __init__(self, workers=5, tmp_suffix='tmp'):
        """Creates empty download manager.

        Args:
            max_workers (int): number of workers to run downloads.

        """
        self.tasks = Queue()
        self.all_tasks = list()

        self.workers = workers
        self.tmp_suffix = tmp_suffix
        self.executor = ThreadPoolExecutor(max_workers=workers + 1)

        self.lock_mkdir = Lock()
        self.lock_stats = Lock()
        self.event_stop = Event()

        self.total_tasks = 0
        self.completed_tasks = 0

    def get_task(self, url, save_to=None, **kwargs):
        """Create a task to add the download queue.

        Args:
            url (str / download.DownloadTask): http or https download url.
            save_to (str): Absolute or relative path to save the file.

        """
        if type(url) is DownloadTask:
            return url

        if save_to is None:
            save_to = url.split('/')[-1]
        save_temp = '{}.{}'.format(save_to, self.tmp_suffix)
        task = DownloadTask(url, save_to, save_temp, **kwargs)
        return task

    def add_task(self, *args, **kwargs):
        """Add a task to the download queue."""
        self.total_tasks += 1
        task = self.get_task(*args, **kwargs)
        self.tasks.put(task)
        self.all_tasks.append(task)

    def start(self):
        """Start all downloads."""
        self.executor.submit(self._stat)
        self.futures = self.executor.map(self._worker, range(self.workers))

    def stop(self):
        """Stop all downloads."""
        for i in range(self.workers):
            self.tasks.put(None)
        for future in self.futures:
            print(future)
        self.event_stop.set()

    @property
    def loaded_bytes(self):
        """float: Sum of loaded bytes across all tasks."""
        return sum(map(lambda task: task.rx_bytes, self.all_tasks))

    @property
    def speed(self):
        """float: Sum of speed across all tasks."""
        return sum(map(lambda task: task.speed, self.all_tasks))

    @property
    def total_bytes(self):
        """float: Sum of total bytes across all tasks."""
        return sum(map(lambda task: task.total_bytes, self.all_tasks))

    def _worker(self, worker=0):
        """Function each worker runs.

        The worker function try to obtain a task and run the download.
        """
        log.debug('worker %d start', worker)
        while True:
            task = self.tasks.get()
            log.debug('get task %s', task)
            if task is None:
                break
            with self.lock_mkdir:
                task.mkdir()
            task.do_download()
        log.debug('worker %d exit', worker)

    def _stat(self, refresh_interval=0.1, speed_past_seconds=3.0):
        """Function a stat thread runs.

        Stat thread periodicly gathers download statistics, and calculate
        speeds.
        """
        while not self.event_stop.wait(refresh_interval):
            period_count = ceil(speed_past_seconds / refresh_interval)
            for task in self.all_tasks:
                task.rx_bytes_history.append(task.rx_bytes)
                peroid_history = task.rx_bytes_history[-period_count:]
                period_loaded = peroid_history[-1] - peroid_history[0]
                period = (len(peroid_history) - 1) * refresh_interval
                task.speed = period_loaded / period

            print(self.loaded_bytes, self.speed)

    def __str__(self):
        """Returns a list of tasks in printable format."""
        return 'Download Tasks:\n' + '\n'.join(str(t) for t in self.tasks)
