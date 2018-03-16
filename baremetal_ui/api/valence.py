from __future__ import absolute_import

import logging
from django.conf import settings

from valenceclient.v1 import client as valence_client
from novaclient import client as nova_client

from openstack_dashboard.api import base
from horizon.utils.memoized import memoized
from horizon.utils.memoized import memoized_with_request

LOG = logging.getLogger(__name__)

@memoized
def valenceclient(request, version=1):
    url = base.url_for(request, 'resource-pooling')
    return valence_client.Client(valence_api_version=version, valence_url=url)
    
def composed_node_list(request):
    return valenceclient(request).nodes.list()
    
def composed_node_get(request, node_uuid):
    return valenceclient(request).nodes.get(node_uuid)
    
def node_compose(request, data):
    return valenceclient(request).nodes.compose(data)
    
def node_decompose(request, node_uuid):
    return valenceclient(request).nodes.decompose(node_uuid)    
    
def os_deploy(request, node_uuid, image_data):
    return valenceclient(request).nodes.deploy_os(node_uuid, image_data)
    
def test(request, msg=None):
    if msg:
        print "Result: %s" % msg
    return valenceclient(request).nodes.test(msg)
    
@memoized
def imageclient(request):
    return valence_client.ImageClient()    
    
def image_list(request, filter=None):
    return imageclient(request).images.list(filter)
    
def get_auth_params_from_request(request):
    """Extracts the properties from the request object needed by the novaclient
    call below. These will be used to memoize the calls to novaclient
    """
    return (
        request.user.username,
        request.user.token.id,
        request.user.tenant_id,
        request.user.token.project.get('domain_id'),
        base.url_for(request, 'compute'),
        base.url_for(request, 'identity')
    )

@memoized_with_request(get_auth_params_from_request)
def novaclient(request_auth_params, version=None):
    (
        username,
        token_id,
        project_id,
        project_domain_id,
        nova_url,
        auth_url
    ) = request_auth_params

    INSECURE = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    CACERT = getattr(settings, 'OPENSTACK_SSL_CACERT', None)

    nova = nova_client.Client(2,
                           username,
                           token_id,
                           project_id=project_id,
                           project_domain_id=project_domain_id,
                           auth_url=auth_url,
                           insecure=INSECURE,
                           cacert=CACERT,
                           http_log_debug=settings.DEBUG,
                           auth_token=token_id,
                           bypass_url=nova_url)
    return nova
    
def compute_service_list(request, binary=None):
    return novaclient(request).services.list(binary=binary)
    
def compute_service_delete(request, service_id):
    novaclient(request).services.delete(service_id)