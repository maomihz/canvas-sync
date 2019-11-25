"""Classes to manage HTTP download tasks."""

from threading import Lock
from queue import Queue

from os.path import dirname
from os import makedirs

from concurrent.futures import ThreadPoolExecutor

import requests


class DownloadManager:
    """Maintains a list of download tasks and run them concurrently."""
    def __init__(self, workers=5):
        """Creates empty download manager.

        Args:
            max_workers (int): number of workers to run downloads.

        """
        self.tasks = Queue()
        self.lock_mkdir = Lock()
        self.workers = workers

    def add_task(self, url, save_to=None):
        """Add a task to the download queue.

        Args:
            url (str): http or https download url.
            save_to (str): Absolute or relative path to save the file.

        """
        if save_to is None:
            save_to = url.split('/')[-1]
        self.tasks.put(DownloadTask(url, save_to))

    def start(self):
        """Start all downloads."""
        # self._worker()
        executor = ThreadPoolExecutor(max_workers=self.workers)
        executor.map(self._worker, range(self.workers))

    def stop(self):
        """Stop all downloads."""
        for i in range(self.workers):
            self.tasks.put(None)

    def _worker(self, worker=0):
        """Function each worker runs.

        The worker function try to obtain a task and run the download.
        """
        print('worker %d start' % worker)
        while True:
            print("wait task")
            task = self.tasks.get()
            print("get task", task)
            if task is None:
                break
            with self.lock_mkdir:
                task.mkdir()
            task.do_download()
        print('worker %d done' % worker)

    def __str__(self):
        """Returns a list of tasks in printable format."""
        return 'Download Tasks:\n' + '\n'.join(str(t) for t in self.tasks)


class DownloadTask:
    """A task for download consisting of a local path and a URL."""
    def __init__(self, url, save_to):
        self.save_to = save_to
        self.url = url

    def mkdir(self):
        """Recursively makes directory required by the download task."""
        if self.save_dir:
            makedirs(self.save_dir, exist_ok=True)

    def do_download(self, chunk_size=2048):
        print('do download')
        with requests.get(self.url, stream=True) as r:
            r.raise_for_status()
            with open(self.save_to, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
        print('done')

    @property
    def save_dir(self):
        """str: directory of the file to save."""
        return dirname(self.save_to)

    def __str__(self):
        """Describe the download task in a printable format."""
        return '{} -> {}'.format(self.url, self.save_to)
