from canvas_sync import log

from os.path import dirname
import os

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

    def mkdir(self):
        """Recursively makes directory required by the download task."""
        if self.save_dir:
            os.makedirs(self.save_dir, exist_ok=True)
        if self.save_dir_temp:
            os.makedirs(self.save_dir, exist_ok=True)

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
        try:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
        finally:
            f.close()
        if self.mtime is not None:
            os.utime(self.save_temp, (self.mtime, self.mtime))
        os.rename(self.save_temp, self.save_to)
        log.debug('download done')

    def __str__(self):
        """Describe the download task in a printable format."""
        return '{} -> {}'.format(self.url, self.save_to)
