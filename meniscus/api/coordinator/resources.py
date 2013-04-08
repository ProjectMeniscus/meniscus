
import falcon

from datetime import datetime, timedelta

from meniscus.api import abort
from meniscus.api import ApiResource
from meniscus.api import format_response_body
from meniscus.api import load_body
from meniscus.api.personalities import PERSONALITIES
from meniscus.data.model.worker import Worker


def _personality_not_valid():
    """
    sends an http 400 invalid personality request
    """
    abort(falcon.HTTP_400, 'invalid personality.')


def _registration_not_valid():
    """
    sends an http 400 invalid registration request
    """
    abort(falcon.HTTP_400, 'invalid registration request.')


def _worker_not_found():
    """
    sends an http 404 invalid worker not found
    """
    abort(falcon.HTTP_404, 'unable to locate worker.')


class WatchlistItem(object):
    def __init__(self, worker_id, last_changed=None, watch_count=None,
                 _id=None, ):

        self.worker_id = worker_id
        self._id = _id

        if _id is None:
            self.last_changed = datetime.now()
            self.watch_count = 1
        else:
            self.last_changed = last_changed
            self.watch_count = watch_count

    def format(self):
        return {
            'worker_id': self.worker_id,
            'last_changed': self.last_changed,
            'watch_count': self.watch_count,
        }

    def format_for_save(self):
        worker_dict = self.format()
        worker_dict['_id'] = self._id
        return worker_dict


class WorkerRoutingResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def broadcast_config_change(self, worker_id):
        """
        Broadcast configuration change to all workers upstream from
        failed offline worker
        """
        worker_dict = self.db.find_one('worker', {'worker_id': worker_id})
        worker = Worker(**worker_dict)
        upstream_list = [p['personality'] for p in PERSONALITIES
                         if p['downstream'] == worker.personality
                         or p['alternate'] == worker.personality]
        upstream_workers = self.db.find(
            'worker', {'personality': {'$in': upstream_list}})

        return [Worker(**worker).get_pipeline_info()
                for worker in upstream_workers]

    def on_put(self, req, resp, worker_id):
        # threshold for expiration
        THRESHOLD_SECONDS = 60
        WATCH_COUNT_THRESHOLD = 5

        threshold = datetime.now() - timedelta(seconds=THRESHOLD_SECONDS)

        # flush out all expired workers
        self.db.delete('watchlist', {'last_changed': {'$lt': threshold}})

        # check for current worker
        worker_dict = self.db.find_one('watchlist', {'worker_id': worker_id})
        if not worker_dict:
            # add new watchlist entry
            watch_item = WatchlistItem(worker_id)
            self.db.put('watchlist', watch_item.format())
        else:
            if worker_dict['watch_count'] == WATCH_COUNT_THRESHOLD:
                self.broadcast_config_change(worker_id)

            updated_worker = WatchlistItem(worker_id,
                                           datetime.now(),
                                           worker_dict['watch_count'] + 1,
                                           worker_dict['_id'])
            self.db.update('watchlist', updated_worker.format_for_save())

        resp.status = falcon.HTTP_202


class WorkerRegistrationResource(ApiResource):

    def __init__(self, db_handler):
        """
        initializes db_handler
        """
        self.db = db_handler

    def _validate_req_body_on_post(self, body):
        """
        validate request body
        """
        try:
            worker = Worker(**body['worker_registration'])

            if worker.personality not in [p['personality']
                                          for p in PERSONALITIES]:
                _personality_not_valid()
        except (KeyError, ValueError, TypeError):
            _registration_not_valid()

    def on_post(self, req, resp):
        """
        receives json req to register worker responds with a 202 for success
        """

        #load json payload in body
        body = load_body(req)

        self._validate_req_body_on_post(body)

        #instantiate new worker object
        new_worker = Worker(**body['worker_registration'])

        #persist the new worker
        self.db.put('worker', new_worker.format())

        resp.status = falcon.HTTP_202
        resp.body = format_response_body(
            new_worker.get_registration_identity())


class WorkerConfigurationResource(ApiResource):
    """
    configuration: listing of all workers downstream of the worker
    passes configuration to a worker based on the workers personality
    """

    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, worker_id):
        """
        Gets configuration e.g. list of downstream personalities in the grid
        """
        #todo: rename list of valid worker statuses for routing
        VALID_ROUTE_LIST = ['online', 'draining']
        worker_dict = self.db.find_one(
            'worker', {'worker_id': worker_id})
        if not worker_dict:
            _worker_not_found()

        worker = Worker(**worker_dict)

        default = [p['downstream'] for p in PERSONALITIES
                   if p['personality'] == worker.personality]
        alternate = [p['alternate'] for p in PERSONALITIES
                     if p['personality'] == worker.personality]

        downstream = default + alternate
        downstream_workers = self.db.find(
            'worker', {'personality': {'$in': downstream},
                       'status': {'$in': VALID_ROUTE_LIST}})

        pipeline = [
            Worker(**worker).get_pipeline_info()
            for worker in downstream_workers]

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'pipeline_workers': pipeline})
