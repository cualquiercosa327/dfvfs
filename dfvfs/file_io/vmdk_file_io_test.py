#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The dfVFS Project Authors.
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
"""Tests for the file-like object implementation using pyvmdk."""

import os
import unittest

from dfvfs.file_io import test_lib
from dfvfs.path import os_path_spec
from dfvfs.path import vmdk_path_spec


class VmdkFileTest(test_lib.ImageFileTestCase):
  """The unit test for the VMDK image file-like object."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    super(VmdkFileTest, self).setUp()
    test_file = os.path.join('test_data', 'image.vmdk')
    path_spec = os_path_spec.OSPathSpec(location=test_file)
    self._vmdk_path_spec = vmdk_path_spec.VmdkPathSpec(parent=path_spec)

  def testOpenCloseInode(self):
    """Test the open and close functionality using an inode."""
    self._TestOpenCloseInode(self._vmdk_path_spec)

  def testOpenCloseLocation(self):
    """Test the open and close functionality using a location."""
    self._TestOpenCloseLocation(self._vmdk_path_spec)

  def testSeek(self):
    """Test the seek functionality."""
    self._TestSeek(self._vmdk_path_spec)

  def testRead(self):
    """Test the read functionality."""
    self._TestRead(self._vmdk_path_spec)


if __name__ == '__main__':
  unittest.main()
