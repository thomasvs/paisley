# -*- test-case-name: paisley.tests.test_views -*-
# Copyright (c) 2007-2008
# See LICENSE for details.

"""
Object mapping view API.
"""


class View(object):
    def __init__(self, couch, dbName, docId, viewId, objectFactory):
        """
        objectFactory should implement fromDict, taking a dictionary containing
        key and value.
        """
        self._couch = couch
        self._dbName = dbName
        self._docId = docId
        self._viewId = viewId
        self._objectFactory = objectFactory

    def _mapObjects(self, results):
        for x in results:
            obj = self._objectFactory()
            obj.fromDict(x)
            yield obj

    def queryView(self):
        d = self._couch.openView(
            self._dbName,
            self._docId,
            self._viewId,
            )
        d.addCallback(self._mapObjects)
        return d
