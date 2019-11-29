"""Command line interface to the canvas sync program."""
from .sync import Sync
from os import getenv
from canvas_sync import log
import argparse


API_URL = getenv('CANVAS_API_URL')
API_KEY = getenv('CANVAS_API_KEY')


def main():
    parser = argparse.ArgumentParser(description='Sync files from canvas.')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)

    args = parser.parse_args()

    if not API_URL or not API_KEY:
        print('Canvas API keys are missing!')
        return

    # -vvv = debug
    log.setLevel(40 - args.verbose * 10)
    sync = Sync()
    print('Loading the list of files to sync...')
    sync.add_api_user(API_URL, API_KEY, limit=args.limit)

    print('Starting to sync files...')
    for task in sync.sync_files:
        log.debug(task)
    sync.sync()
