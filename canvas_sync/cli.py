"""Command line interface to the canvas sync program."""
from .sync import Sync
from os import getenv


API_URL = getenv('CANVAS_API_URL')
API_KEY = getenv('CANVAS_API_KEY')


def main():
    if not API_URL or not API_KEY:
        print('Canvas API keys are missing!')
        return
    sync = Sync()
    sync.add_api_user(API_URL, API_KEY)
    for task in sync.sync_files:
        print(task)
    sync.sync()
