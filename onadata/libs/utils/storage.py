# coding: utf-8
import os
import shutil

from django.core.files.storage import get_storage_class


def delete_user_storage(username):

    storage = get_storage_class()()

    def _recursive_delete(path):
        directories, files = storage.listdir(path)
        for file_ in files:
            storage.delete(os.path.join(path, file_))
        for directory in directories:
            _recursive_delete(os.path.join(path, directory))

    if storage.__class__.__name__ == 'FileSystemStorage':
        if storage.exists(username):
            shutil.rmtree(storage.path(username))
    else:
        _recursive_delete(username)


