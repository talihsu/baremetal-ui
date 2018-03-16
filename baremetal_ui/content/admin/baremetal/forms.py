import logging

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

LOG = logging.getLogger(__name__)

OPENSTACK_SERVER_ROLE_CHOICES = [
        ("compute", "Compute"),
        ("storage", "Storage"),
        ("network", "Network")
]

class AddNode(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=True)    
    server_role = forms.ChoiceField(label=_("OpenStack Server Role"),
                                        required=True)
    chassis_id = forms.CharField(max_length=16,
                           label=_("Location"),
                           required=False)
                                        
    def __init__(self, request, *args, **kwargs):
        super(AddNode, self).__init__(request, *args, **kwargs)
        
        self.fields["server_role"].choices = OPENSTACK_SERVER_ROLE_CHOICES
        
    def handle(self, request, data):
        # Organize data
        data["properties"] = {}
        if not data["chassis_id"]:
            del data["chassis_id"]
        
        # Get specific image for compute node
        try:
            os_name = ""
            if data["server_role"] == "compute":
                os_name = "ubuntu_16.04_compute"
                data["description"] = "[Compute] %s" % data["name"]
            elif data["server_role"] == "storage":
                os_name = "ubuntu_16.04_storage"
                data["description"] = "[Storage] %s" % data["name"]
            elif data["server_role"] == "network":
                os_name = "ubuntu_16.04_network"
                data["description"] = "[Network] %s" % data["name"]
            else:
                raise Exception("Unknown role.")        
        
            _images = api.valence.image_list(request, "os_name=%s" % os_name)
            if len(_images):
                data["actions"] = {
                                    "deploy": {  
                                                "image_id": _images[0]["uuid"],
                                                "bios_mode": "uefi",
                                                "boot_mode": "iscsi"
                                              }
                                  }                
            else:
                raise Exception("No available images for this role.") 

            print data        

            api.valence.node_compose(request, data)
            #api.valence.test(request, "Add compute node: %s" % data)
        except Exception as e:
            redirect = reverse('horizon:admin:baremetal:index')
            exceptions.handle(request, _("Unable to compose a node. %s" % e.message),
                              redirect=redirect)       
        return True
       
    def clean(self):
        return super(AddNode, self).clean()   


