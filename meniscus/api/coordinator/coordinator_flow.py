
from oslo.config import cfg

from meniscus.api.personalities import PERSONALITIES
from meniscus.config import get_config
from meniscus.config import init_config
from meniscus.data.model.worker import Worker
from meniscus.api.coordinator import coordinator_errors as error

# cache configuration options
_COORDINATOR_GROUP = cfg.OptGroup(name='coordinator_settings',
                                  title='Coordinator Settings')
get_config().register_group(_COORDINATOR_GROUP)

_COORDINATOR_CONSTANTS = [
    cfg.ListOpt('valid_route_list',
                default=['online', 'draining'],
                help="""default duration for monitoring failed workers"""
                ),
    cfg.ListOpt('valid_status_list',
                default=['new', 'offline', 'online', 'draining'],
                help="""count of reported failures"""
                )
]

get_config().register_opts(_COORDINATOR_CONSTANTS, group=_COORDINATOR_GROUP)
try:
    init_config()
    conf = get_config()
except cfg.ConfigFilesNotFoundError:
    conf = get_config()

VALID_ROUTE_LIST = conf.coordinator_settings.valid_route_list
VALID_STATUS_LIST = conf.coordinator_settings.valid_status_list


# worker registration resource
def validate_worker_registration_req_body(body):
    """
    validate request body
    """
    try:
        worker = Worker(**body['worker_registration'])

        if worker.personality not in [p['personality']for p in PERSONALITIES]:
            error._personality_not_valid()
    except (KeyError, ValueError, TypeError):
        error._registration_not_valid()


def add_worker(db, new_worker_object):
    """
    add new worker to db
    """
    db.put('worker', new_worker_object.format())


def find_worker(db, worker_id):
    """
    returns worker object based on worker id
    """
    worker_dict = db.find_one('worker', {'worker_id': worker_id})
    if not worker_dict:
        error._worker_not_found()
    return Worker(**worker_dict)
