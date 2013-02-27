import falcon

from meniscus.api import ApiResource, abort


def _header_not_valid():
    abort(falcon.HTTP_401, 'unauthorized request')


def _role_not_valid():
    abort(falcon.HTTP_403, 'roles do not have access to this resource')


class NodeConfigurationResource(ApiResource):

    def on_get(self, req, resp):

        VALID_HEADER = 'X-Auth-Roles'
        VALID_ROLE = 'meniscus_role'

        roles = req.get_header(VALID_HEADER)

        if not roles:
            _header_not_valid()

        has_access = False

        for role in roles:
            if role == VALID_ROLE:
                has_access = True
                break

        if has_access:
            resp.status = falcon.HTTP_200
        else:
            _role_not_valid()
