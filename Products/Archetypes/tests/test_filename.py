# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################
"""
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

from Products.Archetypes.tests.attestcase import ATTestCase
from Products.Archetypes.tests.utils import PACKAGE_HOME

from Products.Archetypes.tests.test_classgen import Dummy
from Products.Archetypes.tests.test_classgen import gen_dummy
from Products.Archetypes.tests.test_classgen import default_text

from Products.Archetypes.atapi import *


class GetFilenameTest(ATTestCase):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()

    def test_textfieldwithfilename(self):
        obj = self._dummy
        field = obj.getField('atextfield')
        self.assertEqual(field.getFilename(obj), '')
        self.assertEqual(field.getRaw(obj), default_text)
        obj.setAtextfield('Bla', filename='name.rst')
        self.assertEqual(field.getFilename(obj), 'name.rst')
        self.assertEqual(field.getRaw(obj), 'Bla')

    def test_textfieldwithfilename2(self):
        obj = self._dummy
        field = obj.getField('atextfield')
        obj.setAtextfield('Ble', filename='eitadiacho.txt')
        self.assertEqual(field.getRaw(obj), 'Ble')
        self.assertEqual(field.getFilename(obj), 'eitadiacho.txt')

    def test_textfieldwithoutfilename(self):
        obj = self._dummy
        field = obj.getField('atextfield')
        obj.setAtextfield('Bli')
        self.assertEqual(str(field.getRaw(obj)), 'Bli')
        self.assertEqual(field.getFilename(obj), '')

    def test_textfielduploadwithoutfilename(self):
        obj = self._dummy
        file = open(os.path.join(PACKAGE_HOME, 'input', 'rest1.tgz'), 'r')
        field = obj.getField('atextfield')
        obj.setAtextfield(file)
        file.close()
        self.assertEqual(field.getFilename(obj), 'rest1.tgz')

    def test_filefieldwithfilename(self):
        obj = self._dummy
        field = obj.getField('afilefield')
        obj.setAfilefield('Blo', filename='beleza.jpg')
        self.assertEqual(str(obj.getAfilefield()), 'Blo')
        self.assertEqual(field.getFilename(obj), 'beleza.jpg')

    def test_filefieldwithfilename2(self):
        obj = self._dummy
        field = obj.getField('afilefield')
        obj.setAfilefield('Blu', filename='juca.avi')
        self.assertEqual(str(obj.getAfilefield()), 'Blu')
        self.assertEqual(field.getFilename(obj), 'juca.avi')

    def test_filefieldwithoutfilename(self):
        obj = self._dummy
        field = obj.getField('afilefield')
        obj.setAfilefield('Blao')
        self.assertEqual(str(obj.getAfilefield()), 'Blao')
        self.assertEqual(field.getFilename(obj), '')

    def test_filefielduploadwithoutfilename(self):
        obj = self._dummy
        file = open(os.path.join(PACKAGE_HOME, 'input', 'rest1.tgz'), 'r')
        field = obj.getField('afilefield')
        obj.setAfilefield(file)
        file.close()
        self.assertEqual(field.getFilename(obj), 'rest1.tgz')


class SetFilenameTest(ATTestCase):

    def afterSetUp(self):
        gen_dummy()
        self._dummy = dummy = Dummy(oid='dummy')
        self._dummy.initializeArchetype()
        file1 = open(os.path.join(PACKAGE_HOME, 'input', 'rest1.tgz'), 'r')
        file2 = open(os.path.join(PACKAGE_HOME, 'input', 'word.doc'), 'r')
        # afilefield is the primary field
        dummy.setAfilefield(file1)
        dummy.setAnotherfilefield(file2)
        file1.close()
        file2.close()

    def testMutatorSetFilename(self):
        obj = self._dummy
        field1 = obj.getField('afilefield')
        field2 = obj.getField('anotherfilefield')
        filename1 = 'rest1.tgz'
        filename2 = 'word.doc'
        self.assertEqual(field1.getFilename(obj), filename1)
        self.assertEqual(field2.getFilename(obj), filename2)

    def testBaseObjectPrimaryFieldSetFilename(self):
        obj = self._dummy
        filename1 = 'eitadiacho.mid'
        filename2 = 'ehagoraoununca.pdf'
        obj.setFilename(filename1)
        obj.setFilename(filename2, 'anotherfilefield')
        self.assertEqual(obj.getFilename(), filename1)
        self.assertEqual(obj.getFilename('afilefield'), filename1)
        self.assertEqual(obj.getFilename('anotherfilefield'), filename2)

    def testBaseObjectSetFilename(self):
        obj = self._dummy
        filename1 = 'masbahtche.avi'
        filename2 = 'guasco.mpg'
        obj.setFilename(filename1, 'afilefield')
        obj.setFilename(filename2, 'anotherfilefield')
        self.assertEqual(obj.getFilename(), filename1)
        self.assertEqual(obj.getFilename('afilefield'), filename1)
        self.assertEqual(obj.getFilename('anotherfilefield'), filename2)

    def testFieldSetFilename(self):
        obj = self._dummy
        field1 = obj.getField('afilefield')
        field2 = obj.getField('anotherfilefield')
        filename1 = 'muamba.gif'
        filename2 = 'noruega.jpg'
        field1.setFilename(obj, filename1)
        field2.setFilename(obj, filename2)
        self.assertEqual(field1.getFilename(obj), filename1)
        self.assertEqual(field2.getFilename(obj), filename2)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(GetFilenameTest))
    suite.addTest(makeSuite(SetFilenameTest))
    return suite

if __name__ == '__main__':
    framework()
