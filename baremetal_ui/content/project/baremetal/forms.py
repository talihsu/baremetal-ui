import logging

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api

LOG = logging.getLogger(__name__)

INSTRUCTION_SET_CHOICES = [
        ("", "Not specified"),
        ("x86", "X86 32-bit"),
        ("x86-64", "X86 64-bit"),
        ("IA-64", "Intel IA-64"),
        ("ARM-A32", "ARM 32-bit"),
        ("ARM-A64", "ARM 64-bit"),
        ("MIPS32", "MIPS 32-bit"),
        ("MIPS64", "MIPS 64-bit")   
]

class ComposeNode(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255,
                           label=_("Name"),
                           required=True)
    description = forms.CharField(max_length=255,
                                widget=forms.Textarea(attrs={'rows': 2}),
                                label=_("Description"),
                                required=False)
    cpu_model = forms.ChoiceField(label=_("CPU Model"),
                                    required=False)
    cpu_cores = forms.IntegerField(label=_("Total CPU Cores"),
                                    min_value=0,
                                    required=False)
    cpu_instru_set = forms.ChoiceField(label=_("CPU Instruction Set"),
                                        required=False)
    cpu_speed = forms.IntegerField(label=_("CPU Speed (MHz)"),
                                    min_value=0,
                                    required=False)
    ram_size = forms.IntegerField(label=_("Memory Size (GB)"),
                                    min_value=0,
                                    required=False)
    local_drive_type = forms.ChoiceField(label=_("Local Drive Type"),
                                        required=False)
    #local_drive_if = cpu_instru_set = forms.ChoiceField(label=_("Local Drive Interface"),
    #                                    required=False)
    local_drive_size = forms.IntegerField(label=_("Local Drive Size (GB)"),
                                            min_value=0,
                                            required=False)  
    local_drive_count = forms.IntegerField(label=_("Total Local Drives"),
                                            min_value=0,
                                            required=False)
                           
    def __init__(self, request, *args, **kwargs):
        super(ComposeNode, self).__init__(request, *args, **kwargs)
        
        self.fields["cpu_model"].choices = [
            ("", "Not specified"),
            ("Intel(R) Xeon(R) Gold 6130 CPU @ 2.10GHz", "Intel(R) Xeon(R) Gold 6130 CPU @ 2.10GHz"),
            ("Intel(R) Xeon(R) Gold 6138 CPU @ 2.00GHz", "Intel(R) Xeon(R) Gold 6138 CPU @ 2.00GHz")
        ]
        
        self.fields["cpu_instru_set"].choices = INSTRUCTION_SET_CHOICES
        self.fields["local_drive_type"].choices = [("", "Not specified"),
                                                   ("HDD", "HDD"),
                                                   ("SSD", "SSD")] 
        
    def handle(self, request, data):
        # Organize data
        # Add a tag to node name for multi-tenant
        # name-username-tenant_id
        data["name"] = data["name"] + "-" \
                        + request.user.username + "-" \
                        + request.user.tenant_id
                        
        data["properties"] = {}
        
        # CPU
        if data["cpu_model"]:
            data["properties"]["processor"] = {"model": data["cpu_model"]}            
        if data["cpu_cores"]:
            if data["properties"].has_key("processor"):
                data["properties"]["processor"]["total_cores"] = data["cpu_cores"]
            else:
                data["properties"]["processor"] = {"total_cores": data["cpu_cores"]}
        if data["cpu_instru_set"]:
            if data["properties"].has_key("processor"):
                data["properties"]["processor"]["instruction_set"] = data["cpu_instru_set"]
            else:
                data["properties"]["processor"] = {"instruction_set": data["cpu_instru_set"]}
        if data["cpu_speed"]:
            if data["properties"].has_key("processor"):
                data["properties"]["processor"]["speed_mhz"] = data["cpu_speed"]
            else:
                data["properties"]["processor"] = {"speed_mhz": data["cpu_speed"]}
        
        del data["cpu_model"]
        del data["cpu_cores"]
        del data["cpu_instru_set"]
        del data["cpu_speed"]
        
        # RAM
        if data["ram_size"]:
            data["properties"]["memory"] = {"capacity_mib": str(data["ram_size"])}
            
        del data["ram_size"]
        
        # Local drive
        a_drive = {"type": None, "capacity_gb": "0", "interface": None}
        no_type = False
        if data["local_drive_type"]:
            a_drive["type"] = data["local_drive_type"]
        else:
            no_type = True
        
        no_size = False
        if data["local_drive_size"]:
            a_drive["capacity_gb"] = str(data["local_drive_size"])
        else:
            no_size = True
            
        if no_type and no_size:
            data["properties"] = dict()
        else:        
            data["properties"]["local_drives"] = []
            if data["local_drive_count"]:
                for i in xrange(data["local_drive_count"]):
                    data["properties"]["local_drives"].append(a_drive)        
            else:
                data["properties"]["local_drives"].append(a_drive)
        
        del data["local_drive_count"]
        del data["local_drive_size"]
        del data["local_drive_type"]   

        # Special filter
        if data["description"].lower().startswith("location"):
            data["properties"] = {}
            data["chassis_id"] = data["description"].lower().replace("location ", "")
        
        print data
        try:
            api.valence.node_compose(request, data)
            #api.valence.test(request, "Add compute node: %s" % data)
        except Exception as e:
            redirect = reverse('horizon:project:baremetal:index')
            exceptions.handle(request, _("Unable to compose a node. %s" % e.message),
                              redirect=redirect)
                              
        return True
       
    def clean(self):
        return super(ComposeNode, self).clean()   


class DeployOs(forms.SelfHandlingForm):
    node_id = forms.CharField(widget=forms.HiddenInput())
    image_id = forms.ChoiceField(label=_("OS Image"),
                                    required=True)
                           
    def __init__(self, request, *args, **kwargs):
        super(DeployOs, self).__init__(request, *args, **kwargs)
        node_id = kwargs.get('initial', {}).get('node_id')
        self.fields['node_id'].initial = node_id
        
        # List images from image manager
        _images = api.valence.image_list(request, "type=os_image")
        if _images:
            choices = []
            for _image in _images:
                if _image["boot_type"] == "local":
                    choices.append((_image["uuid"], _image["os_name"]+" "+_image["os_version"]))
            
            self.fields["image_id"].choices = choices
            
    def handle(self, request, data):
        # Append necessary arguments
        data["bios_mode"] = "uefi"
        data["boot_mode"] = "local"
        
        print data
        try:
            api.valence.test(request, "Deploy OS: %s" % data)
            #api.valence.os_deploy(request, data["node_id"], data)
        except Exception as e:
            redirect = reverse('horizon:project:baremetal:index')
            exceptions.handle(request, _("Unable to deploy OS. %s" % e.message),
                              redirect=redirect)
            
        return True
        
    def clean(self):
        return super(DeployOs, self).clean()