
import httplib

from datetime import datetime, timedelta

import requests

from meniscus.api.utils.request import http_request
from oslo.config import cfg
from meniscus.api.coordinator import coordinator_flow
from meniscus.api.coordinator import coordinator_errors
from meniscus.api.personalities import PERSONALITIES
from meniscus.config import get_config
from meniscus.config import init_config
from meniscus.data.model.worker import WatchlistItem
from meniscus.data.model.worker import Worker
from meniscus.openstack.common import jsonutils


# cache configuration options
_WATCHLIST_GROUP = cfg.OptGroup(name='watchlist_settings',
                                title='Watchlist Settings')
get_config().register_group(_WATCHLIST_GROUP)

_WATCHLIST_THRESHOLDS = [
    cfg.IntOpt('failure_tolerance_seconds',
               default=60,
               help="""default duration for monitoring failed workers"""),
    cfg.IntOpt('watchlist_count_threshold',
               default=5,
               help="""count of reported failures""")
]

get_config().register_opts(_WATCHLIST_THRESHOLDS, group=_WATCHLIST_GROUP)
try:
    init_config()
    conf = get_config()
except cfg.ConfigFilesNotFoundError:
    conf = get_config()

FAILURE_TOLERANCE_SECONDS = conf.watchlist_settings.failure_tolerance_seconds
WATCHLIST_COUNT_THRESHOLD = conf.watchlist_settings.watchlist_count_threshold


def _add_watchlist_item(db, watch_item):
    """
    adds item to watchlist
    """
    db.put('watchlist', watch_item.format())


def _update_watchlist_item(db, watch_item):
    """
    updates watch count and last changed for watchlist item
    """
    db.update('watchlist', watch_item.format_for_save())


def _delete_expired_watchlist_items(db):
    """
    deletes all expired watchlist items when method is called with respect to
    the threshold constant
    """
    threshold = datetime.now() - timedelta(seconds=FAILURE_TOLERANCE_SECONDS)

    # flush out all expired workers
    db.delete('watchlist', {'last_changed': {'$lt': threshold}})


def _get_broadcaster_list(db):
    broadcaster_list = db.find(
        'worker', {'personality': 'broadcaster',
                   'status': {'$in': coordinator_flow.VALID_ROUTE_LIST}})

    if not broadcaster_list:
        return []

    broadcaster_workers = [Worker(**worker).ip_address_v4
                           for worker in broadcaster_list]

    return broadcaster_workers


def _get_broadcast_targets(db, worker):
    """
    builds list of worker callback addresses for config change broadcast
    """

    upstream_personality_list = [p['personality'] for p in PERSONALITIES
                                 if p['downstream'] == worker.personality
                                 or p['alternate'] == worker.personality]

    if not upstream_personality_list:
        return False

    upstream_list = db.find(
        'worker', {'personality': {'$in': upstream_personality_list},
                   'status': {'$in': coordinator_flow.VALID_ROUTE_LIST}})

    if not upstream_list:
        return False

    upstream_workers = [Worker(**worker) for worker in upstream_list]

    broadcast = {
        "type": "ROUTES",
        "targets": [target.callback for target in upstream_workers]
    }

    if not broadcast['targets']:
        return False

    return {"broadcast": broadcast}


def _send_target_list_to_broadcaster(db, worker):
    """
    send broadcast list to broadcaster
    """

    # list of broadcasters
    broadcasters = _get_broadcaster_list(db)
    if not broadcasters:
        ## todo log no online broadcasters
        return False

    # list of broadcast targets
    broadcast_targets = _get_broadcast_targets(db, worker)
    if not broadcast_targets:
        ## todo: log failed to find target
        return False

    for broadcaster_uri in broadcasters:

        try:
            ## todo refactor callback address to not include /v1/callback/"
            resp = http_request(
                'http://{0}:8080/v1/broadcast'.format(broadcaster_uri),
                json_payload=jsonutils.dumps(broadcast_targets),
                http_verb='PUT')
            if resp.status_code == httplib.OK:
                return True
        except requests.RequestException:
            ## todo Log broadcaster connection failure
            pass

    ## todo Log no broadcasters available
    return False


def process_watchlist_item(db, worker_id):
    """
    process a worker id with respect to the watchlist table.
    delete expired watchlist items
    add or update watchlist entry
    broadcast new worker configuration if watch_count is met
    """

    _delete_expired_watchlist_items(db)

    watch_dict = db.find_one('watchlist', {'worker_id': worker_id})
    if not watch_dict:
        watch_item = WatchlistItem(worker_id)
        _add_watchlist_item(db, watch_item)
    else:
        watch_item = WatchlistItem(watch_dict['worker_id'],
                                   watch_dict['last_changed'],
                                   watch_dict['watch_count'],
                                   watch_dict['_id'])
        watch_item.increment()
        _update_watchlist_item(db, watch_item)

    # update watchlist entry
    if watch_item.watch_count == WATCHLIST_COUNT_THRESHOLD:
        worker = coordinator_flow.find_worker(db, worker_id)

        if worker.status != 'offline':
            coordinator_flow.update_worker_status(db, worker, 'offline')
            _send_target_list_to_broadcaster(db, worker)
