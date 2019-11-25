
from canvas_sync.downloadmanager import DownloadManager

dl = DownloadManager(workers=6)
dl.start()
dl.add_task('http://gnu.mirror.constant.com/coreutils/coreutils-8.10.tar.gz')
dl.add_task('http://gnu.mirror.constant.com/coreutils/coreutils-8.10.tar.gz.sig')
dl.add_task('http://gnu.mirror.constant.com/coreutils/coreutils-8.11.tar.gz')
dl.add_task('http://gnu.mirror.constant.com/coreutils/coreutils-8.11.tar.gz.sig')
dl.add_task('http://gnu.mirror.constant.com/coreutils/coreutils-8.12.tar.gz')
dl.add_task('http://gnu.mirror.constant.com/coreutils/coreutils-8.12.tar.gz.sig')
dl.add_task('http://gnu.mirror.constant.com/coreutils/coreutils-8.13.tar.gz')
dl.add_task('http://gnu.mirror.constant.com/coreutils/coreutils-8.13.tar.gz.sig')
dl.add_task('http://gnu.mirror.constant.com/coreutils/coreutils-8.14.tar.xz')
dl.add_task('http://gnu.mirror.constant.com/coreutils/coreutils-8.14.tar.xz.sig')
dl.add_task('http://gnu.mirror.constant.com/coreutils/coreutils-8.15.tar.xz')
dl.add_task('http://gnu.mirror.constant.com/coreutils/coreutils-8.15.tar.xz.sig')
dl.stop()
