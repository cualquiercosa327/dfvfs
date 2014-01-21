#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The dfVFS Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The SleuthKit (TSK) partition file entry implementation."""

# This is necessary to prevent a circular import.
import dfvfs.file_io.tsk_partition_file_io

from dfvfs.lib import definitions
from dfvfs.lib import errors
from dfvfs.lib import tsk_partition
from dfvfs.path import tsk_partition_path_spec
from dfvfs.vfs import file_entry
from dfvfs.vfs import vfs_stat


class TSKPartitionDirectory(file_entry.Directory):
  """Class that implements a directory object using pytsk3."""

  def _EntriesGenerator(self):
    """Retrieves directory entries.

       Since a directory can contain a vast number of entries using
       a generator is more memory efficient.

    Yields:
      A path specification (instance of path.TSKPartitionPathSpec).
    """
    # Only the virtual root file has directory entries.
    part_index = getattr(self.path_spec, 'part_index', None)
    start_offset = getattr(self.path_spec, 'start_offset', None)

    if part_index is not None or start_offset is not None:
      return

    location = getattr(self.path_spec, 'location', None)
    if location is None or location != self._file_system.LOCATION_ROOT:
      return

    tsk_volume = self._file_system.GetTSKVolume()
    bytes_per_sector = tsk_partition.TSKVolumeGetBytesPerSector(tsk_volume)
    part_index = 0
    partition_index = 0

    # pytsk3 does not handle the Volume_Info iterator correctly therefore
    # the explicit list is needed to prevent the iterator terminating too
    # soon or looping forever.
    for tsk_vs_part in list(tsk_volume):
      kwargs = {}

      if tsk_partition.TSKVsPartIsAllocated(tsk_vs_part):
        partition_index += 1
        kwargs['location'] = u'/p{0:d}'.format(partition_index)

      kwargs['part_index'] = part_index
      part_index += 1

      start_sector = tsk_partition.TSKVsPartGetStartSector(tsk_vs_part)

      if start_sector is not None:
        kwargs['start_offset'] = start_sector * bytes_per_sector

      kwargs['parent'] = self.path_spec.parent

      yield tsk_partition_path_spec.TSKPartitionPathSpec(**kwargs)


class TSKPartitionFileEntry(file_entry.FileEntry):
  """Class that implements a file entry object using pytsk3."""

  TYPE_INDICATOR = definitions.TYPE_INDICATOR_TSK_PARTITION

  def __init__(self, file_system, path_spec, is_root=False, is_virtual=False):
    """Initializes the file entry object.

    Args:
      file_system: the file system object (instance of vfs.FileSystem).
      path_spec: the path specification (instance of path.PathSpec).
      is_virtual: optional boolean value to indicate if the file entry is
                  a virtual file entry emulated by the corresponding file
                  system. The default is False.
      tar_info: optional tar info object (instance of tarfile.TarInfo).
                The default is None.
    """
    super(TSKPartitionFileEntry, self).__init__(
        file_system, path_spec, is_root=is_root, is_virtual=is_virtual)
    self._file_object = None
    self._name = None
    self._tsk_vs_part = None

  def _GetDirectory(self):
    """Retrieves the directory object (instance of TSKPartitionDirectory)."""
    if self._stat_object is None:
      self._stat_object = self._GetStat()

    if (self._stat_object and
        self._stat_object.type == self._stat_object.TYPE_DIRECTORY):
      return TSKPartitionDirectory(self._file_system, self.path_spec)
    return

  def _GetStat(self):
    """Retrieves the stat object.

    Returns:
      The stat object (instance of vfs.VFSStat).

    Raises:
      BackEndError: when the tsk volume system part is missing in a non-virtual
                    file entry.
    """
    if self._tsk_vs_part is None:
      self._tsk_vs_part = self.GetTSKVsPart()

    stat_object = vfs_stat.VFSStat()

    if not self._is_virtual and self._tsk_vs_part is None:
      raise errors.BackEndError(
          u'Missing tsk volume system part in non-virtual file entry.')

    tsk_volume = self._file_system.GetTSKVolume()
    bytes_per_sector = tsk_partition.TSKVolumeGetBytesPerSector(tsk_volume)

    # File data stat information.
    if self._tsk_vs_part is not None:
      number_of_sectors = tsk_partition.TSKVsPartGetNumberOfSectors(
          self._tsk_vs_part)

      if number_of_sectors:
        stat_object.size = number_of_sectors * bytes_per_sector

    # Date and time stat information.

    # Ownership and permissions stat information.

    # File entry type stat information.

    # The root file entry is virtual and should have type directory.
    if self._is_virtual:
      stat_object.type = stat_object.TYPE_DIRECTORY
    else:
      stat_object.type = stat_object.TYPE_FILE

    if not self._is_virtual:
      stat_object.is_allocated = tsk_partition.TSKVsPartIsAllocated(
          self._tsk_vs_part)

    return stat_object

  @property
  def name(self):
    """"The name of the file entry, which does not include the full path."""
    if self._name is None:
      # Directory entries without a location in the path specification
      # are not given a name for now.
      location = getattr(self.path_spec, 'location', None)
      if location is not None:
        self._name = self._file_system.BasenamePath(location)
      else:
        self._name = u''
    return self._name

  @property
  def sub_file_entries(self):
    """The sub file entries (generator of instance of vfs.FileEntry)."""
    if self._directory is None:
      self._directory = self._GetDirectory()

    if self._directory:
      for path_spec in self._directory.entries:
        yield TSKPartitionFileEntry(self._file_system, path_spec)

  def GetFileObject(self):
    """Retrieves the file-like object (instance of file_io.FileIO)."""
    if self._file_object is None:
      if self._tsk_vs_part is None:
        self._tsk_vs_part = self.GetTSKVsPart()

      tsk_volume = self._file_system.GetTSKVolume()
      self._file_object = dfvfs.file_io.tsk_partition_file_io.TSKPartitionFile(
          tsk_volume, self._tsk_vs_part)
      self._file_object.open()
    return self._file_object

  def GetParentFileEntry(self):
    """Retrieves the parent file entry."""
    return

  def GetTSKVsPart(self):
    """Retrieves the TSK volume system part object.

    Returns:
      A TSK volume system part object (instance of pytsk3.TSK_VS_PART_INFO)
      or None.
    """
    tsk_volume = self._file_system.GetTSKVolume()
    tsk_vs_part, _ = tsk_partition.GetTSKVsPartByPathSpec(
        tsk_volume, self.path_spec)
    return tsk_vs_part