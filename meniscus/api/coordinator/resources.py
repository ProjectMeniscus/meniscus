
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


class WorkerAlert(object):
    def __init__(self, worker_id, last_changed=None, alert_ct=None,
                 _id=None, ):
        if _id is None:
            self.worker_id = worker_id
            self.last_changed = datetime.now()
            self.alert_ct = 1
        else:
            self._id = _id
            self.worker_id = worker_id
            self.last_changed = last_changed
            self.alert_ct = alert_ct

    def format(self):
        return {
            'worker_id': self.worker_id,
            'last_changed': self.last_changed,
            'alert_ct': self.alert_ct
        }

    def format_for_save(self):
        worker_dict = self.format()
        worker_dict['_id'] = self._id
        return worker_dict


class WorkerRoutingResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def _get_upstream(self, alert_personality):
        """ get upstream workers """
        upstream_list = [{'personality': personality['personality']}
                         for personality in PERSONALITIES
                         if personality['downstream'] == alert_personality
                         or personality['alternate'] == alert_personality]
        print upstream_list

    def broadcast_config_change(self, worker_id):
        """
        Broadcast configuration change to all workers upstream from
        failed offline worker
        """
        print "in broadcast"
        worker_dict = self.db.find_one('worker', {'worker_id': worker_id})

        # worker = Worker(**worker_dict)
        # upstream_list = self._get_upstream(worker.personality)
        # upstream_workers = self.db.find('worker', {'$or': upstream_list})
        # print upstream_list

    def on_put(self, req, resp, worker_id):
        # threshold for expiration
        THRESHOLD_SECONDS = 60
        ALERT_COUNT_THRESHOLD = 5

        threshold = datetime.now() - timedelta(seconds=THRESHOLD_SECONDS)

        #flush out all expired workers
        self.db.delete('alert', {'last_changed': {'$lt': threshold}})

        # check for current worker
        worker_dict = self.db.find_one('alert', {'worker_id': worker_id})
        if not worker_dict:
            #add new alert entry
            worker_alert = WorkerAlert(worker_id)
            self.db.put('alert', worker_alert.format())
        else:
            if worker_dict['alert_ct'] > ALERT_COUNT_THRESHOLD:
                self.broadcast_config_change(worker_id)

            updated_worker = WorkerAlert(worker_id,
                                         datetime.now(),
                                         worker_dict['alert_ct'] + 1,
                                         worker_dict['_id'])
            self.db.update('alert', updated_worker.format_for_save())

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

            if worker.personality not in PERSONALITIES:
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
            'worker', {'personality': {'$in': downstream}})

        pipeline = [
            Worker(**worker).get_pipeline_info()
            for worker in downstream_workers]

        resp.status = falcon.HTTP_200
        resp.body = format_response_body({'pipeline_workers': pipeline})
