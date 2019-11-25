"""Classes to collect canvas files to sync."""
import logging
from os.path import join

import canvasapi
from canvasapi import Canvas


class Sync:
    def __init__(self, sync_base=''):
        """Constructor for Sync class.

        Args:
            sync_base (str): base directory to sync the files. Absolute path
                is recommended, although relative path would also work.

        """
        self.sync_base = sync_base

        # map of object id -> object
        self._files_map = dict()
        self._folders_map = dict()
        self._courses_map = dict()

    def add_course(self, course):
        """Add all files from a Course object.

        Given a specific course object, the method searches the files and
        folders belonging to the course, and remember them. They can be
        used to prepare a list of files to sync later.

        Args:
            course (canvasapi.Course): The course object to add to sync

        """
        files = course.get_files()
        folders = course.get_folders()

        self._courses_map[course.id] = course
        self._files_map.update({f.id: f for f in files})
        self._folders_map.update({folder.id: folder for folder in folders})

    def add_canvas(self, canvas, limit=0):
        """Add all files in all courses from a Canvas object.

        Search courses from a canvas user, and add all courses to the download
        list.

        Args:
            canvas (canvasapi.Canvas): the canvas object for a user.
            limit (int): Limit number of courses from a user excluding failure.

        """
        courses = canvas.get_courses()

        course_count = 0

        for course in courses:
            if limit > 0 and course_count >= limit:
                break
            # If a course is unauthorized, then skip
            try:
                self.add_course(course)
                course_count += 1
            except canvasapi.exceptions.Unauthorized as e:
                logging.warning('%s error: ', course.name)
                logging.warning('%s', e)

    def add_api_user(self, api_url, api_key):
        """Add all files from all courses given the api key.

        The method constructs a canvasapi.Canvas object and call add_canvas().

        Args:
            api_url (str): the base url of the canvas instance.
            api_key (str): User generated API key.

        """
        canvas = Canvas(api_url, api_key)
        self.add_canvas(canvas, 1)

    @property
    def sync_files(self):
        """[(str, str)]: A list of file download infomation for syncing.

        Each file has a download url and a path to save the file to. The list
        consists of (url, save_to) tuple.

        """
        return [
            self._file_download_info(f)
            for f in self._files_map.values()]

    def _file_download_info(self, file_object):
        """Return information needed for download a specific file.

        Args:
            file_object (canvasapi.File): a file object to extract information.

        Returns:
            (url, save_to) tuple.

        """
        url = file_object.url

        # Associate file with folder and course
        folder = self._folders_map[file_object.folder_id]
        course = self._courses_map[folder.context_id]

        # save to 'sync_base/course_name/folder_name/file_name'
        save_to = join(
                self.sync_base,
                course.name.replace('/', ' '),
                folder.full_name,
                file_object.display_name)
        return url, save_to