# -*- coding: utf-8 -*-
"""A data slice interface for file-like objects."""

from __future__ import unicode_literals

import os

from dfvfs.lib import py2to3

class DataSlice(object):
  """Data slice interface for file-like objects."""

  # The maximum allowed size of the read buffer.
  _MAXIMUM_READ_BUFFER_SIZE = 16 * 1024 * 1024

  def __init__(self, file_object):
    """Initializes the data slice.

    Args:
      file_object (FileIO): a file-like object to read from.
    """
    super(DataSlice, self).__init__()
    self._buffer = b''
    self._file_object = file_object
    self._file_object_size = file_object.get_size()

  # Since this class implements Python interface functions, the following
  # functions are in lower case as an exception to the normal naming
  # convention.

  def __enter__(self):
    """Enters a with statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Exits a with statement."""
    return

  def __getitem__(self, key):
    """Retrieves a range of file data.

    Args:
      key (int|slice): offset or range of offsets to retrieve file data from.

    Returns:
      bytes: range of file data.

    Raises:
      TypeError: if the type of the key is not supported.
      ValueError: if the step value of a slice is not None.
    """
    if isinstance(key, py2to3.INTEGER_TYPES):
      if key < 0:
        self._file_object.seek(key, os.SEEK_END)
      else:
        self._file_object.seek(key, os.SEEK_SET)

      return self._file_object.read(1)

    if not isinstance(key, slice):
      raise TypeError('Unsupported key type: {0!s}'.format(type(key)))

    if key.step is not None:
      raise ValueError('Unsupported slice step: {0!s}'.format(key.step))

    start_offset = key.start or 0
    if start_offset < 0:
      start_offset = 0

    end_offset = key.stop or self._file_object.get_size()

    if end_offset < 0:
      self._file_object.seek(end_offset, os.SEEK_END)
      read_size = -(start_offset - end_offset)

    else:
      self._file_object.seek(start_offset, os.SEEK_SET)
      read_size = end_offset - start_offset

    return self._file_object.read(read_size)