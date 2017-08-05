# -*- coding: utf-8 -*-
# Copyright (c) 2017 Thomas Thurman
# See LICENSE.txt for details.

"""Unit tests for the dictionary cache."""

import unittest
import tempfile
import os
import sys

from plover.dictcache import CollectionCache

THREESOME = {
        'FRED': 'fred',
        'JIM': 'jim',
        'SHEILA': 'sheila',
        }

STANDARD_DB_NAME = 'fred-jim-sheila'
STANDARD_DB_TIMESTAMP = 177

def standard_db(c):
    db = c.get_dictionary(STANDARD_DB_NAME,
            STANDARD_DB_TIMESTAMP)
    db.update(THREESOME.items())

    return db

class CollectionCacheForTesting(object):

    def __enter__(self):
        self.dirname = tempfile.mkdtemp(suffix='dictcache')
        self.dbname = os.path.join(self.dirname, "test.sqlite3")
        self.db = CollectionCache(self.dbname)
        return self.db

    def __exit__(self, *args):
        del self.db
        os.unlink(self.dbname)
        os.rmdir(self.dirname)

class CollectionCacheTestCase(unittest.TestCase):

    def test_shouldbefilled(self):
        with CollectionCacheForTesting() as c:

            for case in [
                    { 
                        'db2name': STANDARD_DB_NAME,
                        'db2timestamp': STANDARD_DB_TIMESTAMP,
                        'expectedSBF': False,
                        'expectedLength': 3,
                    },
                    { 
                        'db2name': 'not-'+STANDARD_DB_NAME,
                        'db2timestamp': STANDARD_DB_TIMESTAMP,
                        'expectedSBF': True,
                        'expectedLength': 0,
                    },
                    { 
                        'db2name': STANDARD_DB_NAME,
                        'db2timestamp': STANDARD_DB_TIMESTAMP+1,
                        'expectedSBF': True,
                        'expectedLength': 0,
                    },
                    ]:
                db1 = standard_db(c)

                db2 = c.get_dictionary(case['db2name'],
                        case['db2timestamp'])

                self.assertEqual(db2.should_be_filled(),
                        case['expectedSBF'])
                self.assertEqual(len(db2),
                        case['expectedLength'])

    def test_length(self):

        with CollectionCacheForTesting() as c:
            db = standard_db(c)
            db = c.get_dictionary('red', 1)

            db.update([
                    ('FRED', 'fred'),
                    ('JIM', 'jim'),
                    ('SHEILA', 'sheila')])

            self.assertEqual(len(db), 3)

    def test_longest_key_length(self):

        with CollectionCacheForTesting() as c:
            db = c.get_dictionary('red', 1)

            self.assertEqual(db.longest_key_length(), 0)

            db.update([
                    ('FRED', 'fred'),
                    ('JIM', 'jim'),
                    ('SHEI/LA', 'sheila')])

            self.assertEqual(db.longest_key_length(), 2)

            db.update([
                    ('SPING', 'sping'),
                    ('SPONG', 'spong')])
 
            self.assertEqual(db.longest_key_length(), 2)

            db.update([
                    ('WOM/BAT', 'wombat'),
                    ('TAR/ANT/UL/A', 'bigspider')])
 
            self.assertEqual(db.longest_key_length(), 4)

    def test_iteration(self):

        with CollectionCacheForTesting() as c:
            db = standard_db(c)
            db = c.get_dictionary('red', 1)

            for (x, y) in zip(THREESOME, db):
                self.assertEqual(x, y)

    def test_getitem(self):

        with CollectionCacheForTesting() as c:
            db = standard_db(c)

            self.assertEqual(db['SHEILA'], 'sheila')
            self.assertEqual(db['FRED'],'fred')

            with self.assertRaises(ValueError):
               db['HAZEL']
            
            self.assertEqual(db.get('SHEILA'), 'sheila')
            self.assertEqual(db.get('JIM'),'jim')
            self.assertEqual(db.get('HAZEL'), None)
            self.assertEqual(db.get('ANNE', 'who?'), 'who?')

    def test_clear(self):

        with CollectionCacheForTesting() as c:
            db = standard_db(c)

            self.assertEqual(len(db), 3)

            db.clear()

            self.assertEqual(len(db), 0)

    def test_getitem(self):

        with CollectionCacheForTesting() as c:
            db = standard_db(c)

            self.assertEqual(db['FRED'],'fred')
            self.assertEqual(db['JIM'],'jim')
            self.assertEqual(db['SHEILA'], 'sheila')
            
            db['SHEILA'] = 'mavis'

            self.assertEqual(db['FRED'],'fred')
            self.assertEqual(db['JIM'],'jim')
            self.assertEqual(db['SHEILA'], 'mavis')

    def test_delitem(self):

        with CollectionCacheForTesting() as c:

            for delendum in ['FRED', 'JIM', 'SHEILA']:
                db = standard_db(c)

                self.assertEqual(db.get('FRED'), 'fred')
                self.assertEqual(db.get('JIM'), 'jim')
                self.assertEqual(db.get('SHEILA'), 'sheila')
            
                del db[delendum]

                for survivor in [x for x in THREESOME.keys() if x!=delendum]:
                    self.assertEqual(db.get(survivor), THREESOME[survivor])

                self.assertEqual(db.get(delendum), None)

                db.clear()

    def test_contains(self):
        with CollectionCacheForTesting() as c:
            db = standard_db(c)

            for name in ('FRED', 'JIM', 'SHEILA'):
                self.assertTrue(name in db)

            for name in ('HAZEL', 'JEREMY', 'PARVINDER'):
                self.assertFalse(name in db)

    def test_reverselookup(self):
        with CollectionCacheForTesting() as c:
            db = standard_db(c)

            db['SHEILA'] = 'mary'
            db['MARIGOLD'] = 'mary'
            db['MARYANNE'] = 'mArY'

            for (value, expectRL, expectCRL) in [
                    ('fred', ['FRED'], ['FRED']),
                    ('jim', ['JIM'], ['JIM']),
                    ('mary', ['SHEILA', 'MARIGOLD'],
                        ['SHEILA', 'MARIGOLD', 'MARYANNE']),
                    ]:
                
                self.assertListEqual(sorted(db.reverse_lookup(value)),
                    sorted(expectRL))

                self.assertListEqual(sorted(db.casereverse_lookup(value)),
                    sorted(expectCRL))

            with self.assertRaises(KeyError):
                db.reverse_lookup('sheila')

            with self.assertRaises(KeyError):
                db.casereverse_lookup('sheila')
