# -*- Mode: Python; test-case-name: paisley.test.test_util -*-
# vi:si:et:sw=4:sts=4:ts=4

from twisted.trial import unittest

from paisley.test import util

class ConfigParserTestCase(unittest.TestCase):
    def setUp(self):
        self.config = util.CouchDBConfig()

    def test_getQueryServers(self):
        servers = self.config.parser.items('query_servers')

        # there is no guarantee someone is using couchjs for javascript,
        # but this seems like the least breakable way to test
        for name, arg in servers:
            if name == 'javascript':
                self.failUnless('couchjs' in arg)
