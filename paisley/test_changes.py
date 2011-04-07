# -*- test-case-name: paisley.test_changes -*-
# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4


from twisted.internet import defer
from twisted.trial import unittest

from paisley import client, changes

from paisley import test_util

# ChangeNotifier test lines

TEST_CHANGES = """
{"seq":3934,"id":"cc4fadc922f11ffb5e358d5da2760de2","changes":[{"rev":"1-1e379f46917bc2fc9b9562a58afde75a"}]}
{"changes": [{"rev": "12-7bfdb7016aa8aa0dd0279d3324b524d1"}], "id": "_design/couchdb", "seq": 5823}
{"last_seq":3934}
{"deleted": true, "changes": [{"rev": "2-5e8bd6dae4307ca6f8fcf8afa53e6bc4"}], "id": "27e74762ad0e64d4094f6feea800a826", "seq": 34}
"""

class FakeNotifier(object):
    def __init__(self):
        self.changes = []

    def changed(self, change):
        self.changes.append(change)

class TestStubChangeReceiver(unittest.TestCase):
    def testChanges(self):
        notifier = FakeNotifier()
        receiver = changes.ChangeReceiver(notifier)

        for line in TEST_CHANGES.split("\n"):
            receiver.lineReceived(line)

        self.assertEquals(len(notifier.changes), 3)
        self.assertEquals(notifier.changes[0]["seq"], 3934)
        self.assertEquals(notifier.changes[2]["deleted"], True)

class TestCacheChangeReceiver(test_util.CouchDBTestCase):
    def setUp(self):
        test_util.CouchDBTestCase.setUp(self)

        self._deferred = None

        self.cache = client.MemoryCache()
        self.db = client.CouchDB('localhost', self.port, cache=self.cache)
        return self.db.createDB('test')

    def waitForChange(self):
        self._deferred = defer.Deferred()
        return self._deferred

    def changed(self, change):
        if self._deferred:
            self._deferred.callback(change)
        self._deferred = None

    def testChanges(self):
        notifier = changes.ChangeNotifier(self.db, 'test')
        notifier.addCache(self.cache)
        notifier.addListener(self)

        d = notifier.start()

        # create a doc
        d.addCallback(lambda _: self.db.saveDoc('test', {
            'key': 'value'
        }))
        d.addCallback(lambda r: setattr(self, 'firstid', r['id']))

        # get it a first time; test that cache didn't have it but cached it
        d.addCallback(lambda _: self.db.openDoc('test', self.firstid))
        d.addCallback(lambda r: setattr(self, 'first', r))
        d.addCallback(lambda _: self.assertEquals(self.first['key'], 'value'))
        d.addCallback(lambda _: self.assertEquals(self.cache.lookups, 1))
        d.addCallback(lambda _: self.assertEquals(self.cache.hits, 0))
        d.addCallback(lambda _: self.assertEquals(self.cache.cached, 1))
        
        # get it a second time; test cache did have it
        d.addCallback(lambda _: self.db.openDoc('test', self.firstid))
        d.addCallback(lambda r: self.assertEquals(r['key'], 'value'))
        d.addCallback(lambda _: self.assertEquals(self.cache.lookups, 2))
        d.addCallback(lambda _: self.assertEquals(self.cache.hits, 1))
        d.addCallback(lambda _: self.assertEquals(self.cache.cached, 1))

        # change it; wait for the change to come in
        def changeCallback(_):
            self.first['key'] = 'othervalue'
            d2 = self.waitForChange()
            self.db.saveDoc('test', self.first, docId=self.firstid)
            return d2
        d.addCallback(changeCallback)
        d.addCallback(lambda _: self.assertEquals(self.cache.cached, 0))

        # get it a second time; it was changed, so test cache did not have it
        d.addCallback(lambda _: self.db.openDoc('test', self.firstid))
        d.addCallback(lambda r: self.assertEquals(r['key'], 'othervalue'))
        d.addCallback(lambda _: self.assertEquals(self.cache.lookups, 3))
        d.addCallback(lambda _: self.assertEquals(self.cache.hits, 1))
        d.addCallback(lambda _: self.assertEquals(self.cache.cached, 1))
        
        return d
