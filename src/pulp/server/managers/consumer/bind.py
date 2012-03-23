# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""
Contains bind management classes
"""

from pymongo.errors import DuplicateKeyError
from pulp.server.db.model.gc_consumer import Consumer, Bind
from pulp.server.exceptions import InvalidValue, MissingResource
from pulp.server.managers import factory
from logging import getLogger


_LOG = getLogger(__name__)


class BindManager(object):
    """
    Manage consumer repo/distributor bind.
    """

    def bind(self, consumer_id, repo_id, distributor_id):
        """
        Bind consumer to a specifiec distirbutor associated with a repository.
        @param consumer_id: uniquely identifies the consumer.
        @type consumer_id: str
        @param repo_id: uniquely identifies the repository.
        @type repo_id: str
        @param distributor_id: uniquely identifies a distributor.
        @type distributor_id: str
        @return: The Bind object
        @rtype: L{Bind}
        @raise MissingResource: when any resource found.
        """
        self.__consumer(consumer_id)
        distributor = self.__distributor(repo_id, distributor_id)
        bind = Bind(consumer_id, repo_id, distributor_id)
        collection = Bind.get_collection()
        try:
            collection.save(bind, safe=True)
        except DuplicateKeyError:
            # idempotent
            pass
        return Dict(bind)

    def unbind(self, consumer_id, repo_id, distributor_id):
        """
        Unbind consumer to a specifiec distirbutor associated with a repository.
        @param consumer_id: uniquely identifies the consumer.
        @type consumer_id: str
        @param repo_id: uniquely identifies the repository.
        @type repo_id: str
        @param distributor_id: uniquely identifies a distributor.
        @type distributor_id: str
        @return: The Bind object
        @rtype: L{Bind}
        """
        query = dict(
            consumer_id=consumer_id,
            repo_id=repo_id,
            distributor_id=distributor_id)
        collection = Bind.get_collection()
        bind = collection.find_one(query)
        if bind is None:
            # idempotent
            return
        collection.remove(bind, safe=True)
        return Dict(bind)
        
    def consumer_deleted(self, id):
        """
        Notification that a consumer has been deleted.
        Associated binds are removed.
        @param id: A consumer ID.
        @type id: str
        """
        collection = Bind.get_collection()
        for bind in self.find_by_consumer(id):
            collection.remove(bind, safe=True)
    
    def repo_deleted(self, id):
        """
        Notification that a repository has been deleted.
        Associated binds are removed.
        @param id: A repo ID.
        @type id: str
        """
        deleted = []
        collection = Bind.get_collection()
        for bind in self.find_by_repo(id):
            deleted.append(bind)
            collection.remove(bind, safe=True)
    
    def distributor_deleted(self, repo_id, distributor_id):
        """
        Notification that a distributor has been deleted.
        Associated binds are removed.
        @param repo_id: A Repo ID.
        @type repo_id: str
        @param distributor_id: A Distributor ID.
        @type distributor_id: str
        """
        deleted = []
        collection = Bind.get_collection()
        for bind in self.find_by_distributor(repo_id, distributor_id):
            deleted.append(bind)
            collection.remove(bind, safe=True)

    def find_all(self):
        """
        Find all binds
        @return: A list of all bind
        @rtype: list
        """
        collection = Bind.get_collection()
        cursor = collection.find({})
        return [Dict(b) for b in cursor]

    def find_by_consumer(self, id):
        """
        Find all binds by Consumer ID.
        @param id: A consumer ID.
        @type id: str
        @return: A list of Bind.
        @rtype: list
        """
        collection = Bind.get_collection()
        query = dict(consumer_id=id)
        cursor = collection.find(query)
        return [Dict(b) for b in cursor]

    def find_by_repo(self, id):
        """
        Find all binds by Repo ID.
        @param id: A Repo ID.
        @type id: str
        @return: A list of Bind.
        @rtype: list
        """
        collection = Bind.get_collection()
        query = dict(repo_id=id)
        cursor = collection.find(query)
        return [Dict(b) for b in cursor]

    def find_by_distributor(self, repo_id, distributor_id):
        """
        Find all binds by Distributor ID.
        @param repo_id: A Repo ID.
        @type repo_id: str
        @param distributor_id: A Distributor ID.
        @type distributor_id: str
        @return: A list of Bind.
        @rtype: list
        """
        collection = Bind.get_collection()
        query = dict(
            repo_id=repo_id,
            distributor_id=distributor_id)
        cursor = collection.find(query)
        return [Dict(b) for b in cursor]

    def __consumer(self, id):
        """
        Find the consumer by id.
        @param id: A consumer id.
        @type id: str
        @return: The found model object.
        @raise MissingResource: when not found.
        """
        collection = Consumer.get_collection()
        consumer = collection.find_one({'id':id})
        if consumer is None:
            raise MissingResource(id)
        return consumer


    def __distributor(self, repo_id, distributor_id):
        """
        Find the distributor by id.
        @param repo_id: A repo id.
        @type repo_id: str
        @param distributor_id: A distributor id.
        @type distributor_id: str
        @return: The found model object.
        @raise MissingResource: when not found.
        """
        mgr = factory.repo_distributor_manager()
        dist = mgr.get_distributor(repo_id, distributor_id)
        if dist is None:
            raise MissingResource('/'.join((repo_id, distributor_id)))
        return dist


class Dict(dict):
    """
    Bind dictionary
    """
    def __init__(self, bind):
        dict.__init__(self)
        for k in ('consumer_id', 'repo_id', 'distributor_id'):
            self[k] = bind[k]