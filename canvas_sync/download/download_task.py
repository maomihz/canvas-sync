from canvas_sync import log

from os.path import dirname
import os
import time

from requests import Request, Session, codes


class DownloadTask:
    """A task for download consisting of a local path and a URL."""
    def __init__(self, url, save_to, save_temp, size=None, mtime=None):
        """Create a new download task.

        Args:
            url (str): download url
            save_to (str): path to save the final file.
            save_temp (str): temporary file path for download chunks.
            size (int, optional): file size in bytes.
            mtime (int, optional): modified time in unix timestamp. If
                specified, download will skip if the file on disk is
                newer than the modified time. After download finishes,
                the file's modified time will be set to the value.

        """
        self.url = url
        self.save_to = save_to
        self.save_temp = save_temp
        self.mtime = mtime

        # Received bytes vs. total bytes of the file.
        self.rx_bytes = 0
        self.total_bytes = size

        # History of received bytes, used to calculate speed (bytes / second).
        self.rx_bytes_history = []
        self.speed_period = 3

        self._last_update = 0
        self._state_receiving = False

    def mkdir(self):
        """Recursively makes directory required by the download task."""
        if self.save_dir:
            os.makedirs(self.save_dir, exist_ok=True)
        if self.save_dir_temp:
            os.makedirs(self.save_dir, exist_ok=True)

    def update_stat(self):
        """Update statistics of the file download."""
        # Do not update if not downloading
        if not self.active:
            return
        now = time.time()
        self.rx_bytes_history.append((now, self.rx_bytes))
        self._last_update = now

    @property
    def speed(self):
        """Return calculated speed of the download task."""
        # No bytes difference to calculate
        if len(self.rx_bytes_history) <= 0:
            return 0
        history_len = len(self.rx_bytes_history)
        time0, rx0 = time.time(), self.rx_bytes

        # If no update for some time
        if time0 - self._last_update > self.speed_period:
            return 0

        # Search history until time difference >= period
        for i in reversed(range(history_len)):
            time2, rx2 = self.rx_bytes_history[i]
            dtime = time0 - time2
            if dtime >= self.speed_period:
                break
        return (rx0 - rx2) / dtime

    @property
    def active(self):
        """bool: Whether the task state is active / downloading."""
        return self._state_receiving

    @property
    def save_dir(self):
        """str: directory of the file to save."""
        return dirname(self.save_to)

    @property
    def save_dir_temp(self):
        """str: directory of the temporary file."""
        return dirname(self.save_temp)

    def do_download(self, chunk_size=2048):
        """Run the download task."""
        log.debug('start download... url %s', self.url)

        # Test if destination already exist
        try:
            save_to_stat = os.stat(self.save_to)
            # Compare the modified time
            if self.mtime is None or save_to_stat.st_mtime >= self.mtime:
                log.warn('File %s already exist, skip.', self.save_to)
                return 0
        except FileNotFoundError:
            pass

        # Test download progress
        try:
            temp_stat = os.stat(self.save_temp)
            range_begin = temp_stat.st_size
            log.debug('File already loaded %d bytes.', range_begin)
        except FileNotFoundError:
            range_begin = 0

        # Create request object
        sess = Session()
        req = Request('GET', url=self.url)
        prep = req.prepare()
        if range_begin > 0:
            prep.headers['range'] = 'bytes=%d-' % range_begin

        # Send request
        r = sess.send(prep, stream=True)
        r.raise_for_status()

        # Test for 206 partial content
        if r.status_code == codes.partial_content:
            log.debug('Resume download at %d bytes.', range_begin)
            f = open(self.save_temp, 'ab')
        else:
            log.debug('Not resume download, start over.')
            f = open(self.save_temp, 'wb')

        # Receive content and write to files
        self._state_receiving = True
        try:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:  # filter out keep-alive new chunks
                    self.rx_bytes += len(chunk)
                    f.write(chunk)
        finally:
            f.close()
            self._state_receiving = False
        if self.mtime is not None:
            os.utime(self.save_temp, (self.mtime, self.mtime))
        os.rename(self.save_temp, self.save_to)
        log.debug('download done')
        return self.rx_bytes

    def __str__(self):
        """Describe the download task in a printable format."""
        return '{} -> {}'.format(self.url, self.save_to)
