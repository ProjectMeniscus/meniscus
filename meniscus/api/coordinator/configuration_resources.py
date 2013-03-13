import json
import falcon

from meniscus.api import ApiResource
from meniscus.api import abort


def _personality_not_valid():
    """
    sends an http 400 invalid personality request
    """
    abort(falcon.HTTP_400, 'invalid personality.')


def _worker_not_found():
    """
    sends an http 404 invalid worker not found
    """
    abort(falcon.HTTP_404, 'unable to locate worker.')


class WorkerConfigurationResource(ApiResource):
    """
    configuration: listing of all workers downstream of the worker
    passes configuration to a worker based on the workers personality
    """
    #Dictionary of personalities
    PERSONALITIES = {'COR': 'worker.correlation',
                     'NORM': 'worker.normalization',
                     'STORE': 'worker.storage'}

    def __init__(self, db_handler):
        self.db = db_handler

    def _find_workers(self, personality):
        """
        finds all workers with personality parameter
        """
        worker_list = self.db.find('worker', {'personality': personality})
        return worker_list

    def _get_configuration(self, personality_type):
        """
        gets required configuration based on personality type
        correlation -> normalization,
        normalization -> storage,
        storage -> *data_node
        * = To be defined later
        """
        if personality_type == self.PERSONALITIES['COR']:
            return self._find_workers(self.PERSONALITIES['NORM'])
        elif personality_type == self.PERSONALITIES['NORM']:
            return self._find_workers(self.PERSONALITIES['STORE'])
        elif personality_type == self.PERSONALITIES['STORE']:
            #too be filled in with unique configuration probably storage nodes
            return []
        else:
            _personality_not_valid()

    def _format_configuration(self, configuration):

        worker_list = list()
        for worker in configuration:
            worker_list.append({'hostname': worker['hostname'],
                                'ip_address_v4': worker['ip_address_v4'],
                                'ip_address_v6': worker['ip_address_v6'],
                                'personality': worker['personality']})
        return {'pipeline_workers': worker_list}

    def on_get(self, req, resp, worker_id):
        """
        Gets configuration e.g. list of downstream personalities in the grid
        """
        reg_worker = self.db.find_one(
            'worker', {'worker_id': worker_id})
        if not reg_worker:
            _worker_not_found()

        configuration = self._get_configuration(reg_worker['personality'])
        resp.status = falcon.HTTP_200
        resp.body = json.dumps(self._format_configuration(configuration))
