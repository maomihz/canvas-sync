from canvas_sync import log

from threading import Lock
from queue import Queue

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
        self.lock_mkdir = Lock()
        self.workers = workers
        self.tmp_suffix = tmp_suffix
        self.executor = ThreadPoolExecutor(max_workers=workers)

    def add_task(self, url, save_to=None):
        """Add a task to the download queue.

        Args:
            url (str): http or https download url.
            save_to (str): Absolute or relative path to save the file.

        """
        if save_to is None:
            save_to = url.split('/')[-1]
        save_temp = '{}.{}'.format(save_to, self.tmp_suffix)

        self.tasks.put(DownloadTask(url, save_to, save_temp))

    def start(self):
        """Start all downloads."""
        self.futures = self.executor.map(self._worker, range(self.workers))

    def stop(self):
        """Stop all downloads."""
        for i in range(self.workers):
            self.tasks.put(None)
        for future in self.futures:
            print(future)

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

    def __str__(self):
        """Returns a list of tasks in printable format."""
        return 'Download Tasks:\n' + '\n'.join(str(t) for t in self.tasks)
