import json
import falcon

from meniscus.api import ApiResource, load_body, abort
from meniscus.model.util import find_tenant, find_host, find_host_profile, \
    find_event_producer
from meniscus.model.tenant import Tenant, Host, HostProfile, EventProducer


def _tenant_not_found():
    abort(falcon.HTTP_404, 'Unable to locate tenant.')


def _tenant_already_exists():
    abort(falcon.HTTP_400, 'Tenant already exists.')


def _host_not_found():
    abort(falcon.HTTP_400, 'Unable to locate host.')


def _profile_not_found():
    abort(falcon.HTTP_400, 'Unable to locate host profile.')


def _producer_not_found():
    abort(falcon.HTTP_400, 'Unable to locate event producer.')


class VersionResource(ApiResource):

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'v1': 'current'})


class TenantResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def on_post(self, req, resp):
        body = load_body(req)
        tenant_id = body['tenant_id']

        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if tenant:
            abort(falcon.HTTP_400, 'Tenant with tenant_id {0} '
                  'already exists'.format(tenant_id))

        new_tenant = Tenant(tenant_id)
        self.db.put(new_tenant.format())
        
        resp.status = falcon.HTTP_201
        resp.set_header('Location', '/v1/{0}'.format(tenant_id))


class UserResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id):

        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(tenant.format())

    def on_delete(self, req, resp, tenant_id):
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        self.db.delete(tenant)
        self.db.commit()

        resp.status = falcon.HTTP_200


class HostProfilesResource(ApiResource):
    
    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id):
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200

        #jsonify a list of formatted profiles
        resp.body = json.dumps([p.format() for p in tenant.profiles])

    def on_post(self, req, resp, tenant_id):
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        body = load_body(req)
        profile_name = body['name']

        # Check if the tenant already has a profile with this name
        for profile in tenant.profiles:
            if profile.name == profile_name:
                abort(falcon.HTTP_400, 'Profile with name {0} already exists.'
                      .format(profile.name, profile.get_id()))

        # Create the new profile for the host
        new_host_profile = HostProfile(self.db.nextsequence, profile_name)

        if 'event_producer_ids' in body.keys():
            event_producer_ids = body['event_producer_ids']

            for event_producer_id in event_producer_ids:
                event_producer = find_event_producer(self.db,
                                                     producer_id=
                                                     event_producer_id)
                if not event_producer:
                    _producer_not_found()

                if event_producer in tenant.event_producers:
                    new_host_profile.event_producers.append(event_producer)
                else:
                    _producer_not_found()

        tenant.profiles.append(new_host_profile)
        self.db.update(tenant.format())

        resp.status = falcon.HTTP_201
        resp.set_header('Location',
                        '/v1/{0}/profiles/{1}'
                        .format(tenant_id, new_host_profile.get_id()))


class HostProfileResource(ApiResource):
    
    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id, profile_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the profile exists and belongs to the tenant
        profile = find_host_profile(self.db, profile_id=profile_id)
        if not profile:
            _profile_not_found()

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(profile.format())

    def on_put(self, req, resp, tenant_id, profile_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)
        if not tenant:
            _tenant_not_found()

        #verify the profile exists and belongs to the tenant
        profile = find_host_profile(self.db, profile_id=profile_id)
        if not profile:
            _profile_not_found()

        #load the message
        body = load_body(req)

        #if attributes are present in message, update the profile
        if 'name' in body.keys():
            profile.name = body['name']

        if 'event_producer_ids' in body.keys():
            producer_ids = body['event_producer_ids']

            # if the put is changing event producers
            if producer_ids:

                #abort if any of the event_producers being passed in are not
                # valid event_producers for this tenant
                for producer_id in producer_ids:

                    if producer_id not in \
                            [p.id for p in tenant.event_producers]:
                        _producer_not_found()

                #remove any event producers from the profile
                # that aren't in list of event_producers being passed in
                for producer in profile.event_producers:
                    if producer.id not in producer_ids:
                        profile.event_producers.remove(producer)

                #see if the incoming event_producers are missing from the
                # profile, and
                for pid in producer_ids:
                    if pid not in [p.id for p in profile.event_producers]:
                        profile.event_producers.append(
                            [p for p in tenant.event_producers if p.id == pid][0])

            else:
                profile.event_producers = []

        self.db.commit()
        resp.status = falcon.HTTP_200

    def on_delete(self, req, resp, tenant_id, profile_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the profile exists
        profile = find_host_profile(self.db, id=profile_id,
                                    when_not_found=_profile_not_found)

        #verify the profile belongs to the tenant
        if not profile in tenant.profiles:
            _profile_not_found()

        self.db.delete(profile)
        self.db.commit()

        resp.status = falcon.HTTP_200


class EventProducersResource(ApiResource):
    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id):
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        resp.status = falcon.HTTP_200
        resp.body = json.dumps([p.format() for p in tenant.event_producers])

    def on_post(self, req, resp, tenant_id):
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        body = load_body(req)
        event_producer_name = body['name']
        event_producer_pattern = body['pattern']

        #if durable or encrypted aren't specified, set to False
        if 'durable' in body.keys():
            event_producer_durable = body['durable']
        else:
            event_producer_durable = False

        if 'encrypted' in body.keys():
            event_producer_encrypted = body['encrypted']
        else:
            event_producer_encrypted = False

        # Check if the event_producer already has a profile with this name
        for event_producer in tenant.event_producers:
            if event_producer.name == event_producer_name:
                abort(falcon.HTTP_400,
                      'Producer {0} with name {1} already exists.'
                      .format(event_producer.id, event_producer.name))

        # Create the new profile for the host
        new_event_producer = EventProducer(tenant.id, event_producer_name,
                                           event_producer_pattern,
                                           event_producer_durable,
                                           event_producer_encrypted)

        self.db.add(new_event_producer)
        tenant.event_producers.append(new_event_producer)
        self.db.commit()

        resp.status = falcon.HTTP_201
        resp.set_header('Location',
                        '/v1/{0}/producers/{1}'
                        .format(tenant_id, new_event_producer.id))


class EventProducerResource(ApiResource):

    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id, event_producer_id):
        #verify the tenant exists

        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the event_producer exists
        event_producer = find_event_producer(self.db,
                                             id=event_producer_id,
                                             when_not_found=
                                             _producer_not_found)

        #verify the event_producer belongs to the tenant
        if not event_producer in tenant.event_producers:
            _producer_not_found()

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(event_producer.format())

    def on_put(self, req, resp, tenant_id, event_producer_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id,
                             when_not_found=_tenant_not_found)

        #verify the event_producer exists
        event_producer = find_event_producer(self.db,
                                             id=event_producer_id,
                                             when_not_found=
                                             _producer_not_found)

        #verify the event_producer belongs to the tenant
        if not event_producer in tenant.event_producers:
            _producer_not_found()

        body = load_body(req)

        #if a key is present, update the event_producer with the value
        if 'name' in body.keys():
            event_producer.name = body['name']

        if 'pattern' in body.keys():
            event_producer.pattern = body['pattern']

        if 'durable' in body.keys():
            event_producer.durable = body['durable']

        if 'encrypted' in body.keys():
            event_producer.encrypted = body['encrypted']

        self.db.commit()

        resp.status = falcon.HTTP_200

    def on_delete(self, req, resp, tenant_id, event_producer_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id,
                             when_not_found=_tenant_not_found)

        #verify the event_producer exists
        event_producer = find_event_producer(self.db,
                                             id=event_producer_id,
                                             when_not_found=
                                             _producer_not_found)

        #verify the event_producer belongs to the tenant
        if not event_producer in tenant.event_producers:
            _producer_not_found()

        self.db.delete(event_producer)
        self.db.commit()

        resp.status = falcon.HTTP_200


class HostsResource(ApiResource):
    
    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id):
        tenant = find_tenant(self.db, tenant_id=tenant_id,
                             when_not_found=_tenant_not_found)

        resp.status = falcon.HTTP_200
        resp.body = json.dumps([h.format() for h in tenant.hosts])

    def on_post(self, req, resp, tenant_id):
        tenant = find_tenant(self.db, tenant_id=tenant_id,
                             when_not_found=_tenant_not_found)

        body = load_body(req)
        hostname = body['hostname']
        ip_address = body['ip_address']

        #if profile id is not in post message, then use a null profile
        if 'profile_id' in body.keys():
            profile_id = body['profile_id']
        else:
            profile_id = None
            profile = None

        #if profile id is in post message, then make sure it is valid profile
        if profile_id:
            profile = find_host_profile(self.db, id=profile_id,
                                        when_not_found=_profile_not_found)

        # Check if the tenant already has a host with this hostname
        for host in tenant.hosts:
            if host.hostname == hostname:
                abort(falcon.HTTP_400,
                      'Host with hostname {0} already exists with'
                      ' id={1}'.format(hostname, host.id))

        # Create the new host definition
        new_host = Host(hostname, ip_address, profile)
        
        self.db.add(new_host)
        tenant.hosts.append(new_host)
        self.db().commit()

        resp.status = falcon.HTTP_201
        resp.set_header('Location',
                        '/v1/{0}/hosts/{1}'
                        .format(tenant_id, new_host.id))


class HostResource(ApiResource):
    
    def __init__(self, db_handler):
        self.db = db_handler

    def on_get(self, req, resp, tenant_id, host_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the hosts exists
        host = find_host(self.db, host_id,
                         when_not_found=_host_not_found)

        #verify the host belongs to the tenant
        if not host in tenant.hosts:
            _host_not_found()

        resp.status = falcon.HTTP_200
        resp.body = json.dumps(host.format())

    def on_put(self, req, resp, tenant_id, host_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the hosts exists
        host = find_host(self.db, host_id,
                         when_not_found=_host_not_found)

        #verify the host belongs to the tenant
        if not host in tenant.hosts:
            _host_not_found()

        body = load_body(req)

        if 'hostname' in body.keys():
            host.hostname = body['hostname']

        if 'ip_address' in body.keys():
            host.ip_address = body['ip_address']

        if 'profile_id' in body.keys():
            profile_id = body['profile_id']

            #if profile_id has a new value,
            # find the profile and assign it to the host
            if profile_id:
                profile = find_host_profile(self.db, id=profile_id,
                                            when_not_found=_profile_not_found)
                host.profile = profile

            #if the profile id key passed an empty value,
            # then remove the profile form the host
            else:
                host.profile = None

        self.db.commit()

        resp.status = falcon.HTTP_200

    def on_delete(self, req, resp, tenant_id, host_id):
        #verify the tenant exists
        tenant = find_tenant(self.db, tenant_id=tenant_id)

        if not tenant:
            _tenant_not_found()

        #verify the hosts exists
        host = find_host(self.db, host_id,
                         when_not_found=_host_not_found)

        #verify the host belongs to the tenant
        if not host in tenant.hosts:
            _host_not_found()

        self.db.delete(host)
        self.db().commit()
        resp.status = falcon.HTTP_200
