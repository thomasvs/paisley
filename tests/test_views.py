# Copyright (c) 2008
# See LICENSE for details.

"""
Tests for the object mapping view API.
"""

from twisted.trial.unittest import TestCase
from twisted.internet.defer import succeed
from paisley.views import View


class StubCouch(object):
    """
    A stub couchdb object that will return preset dictionaries
    """

    def __init__(self, views=None):
        self._views = views

    def openView(self, dbName, docId, viewId, **kwargs):
        return succeed(self._views[viewId])


class Tag(object):
    def fromDict(self, dictionary):
        self.name = dictionary['key']
        self.count = dictionary['value']


class ViewTests(TestCase):
    def test_queryView(self):
        """
        Test that a querying a view gives us an iterable of our user defined
        objects.
        """
        fc = StubCouch(views={'all_tags': [{'key':'foo', 'value':3},
                                           {'key':'bar', 'value':2},
                                           {'key':'baz', 'value':1}]})

        v = View(fc, None, None, 'all_tags', Tag)

        def _checkResults(results):
            self.assertEquals(len(list(results)), 3)

            for tag in results:
                self.assertIn({'key':tag.name, 'value':tag.count},
                              fc._views['all_tags'])

        d = v.queryView()
        d.addCallback(_checkResults)
        return d