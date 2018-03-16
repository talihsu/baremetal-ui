import logging

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from django.utils.translation import pgettext_lazy

from django import template

from openstack_dashboard import api

from horizon import exceptions
from horizon import tables
from horizon.templatetags import sizeformat

LOG = logging.getLogger(__name__)


def is_decomposing(request, node):
    # To do: Get node status
    return False

    
def untag_node_name(request, node):
    node.name = node.name.replace("-" + request.user.username + \
                                "-" + request.user.tenant_id, "")
    return node


class ComposeNode(tables.LinkAction):
    name = "compose"
    verbose_name = _("Compose Node")
    url = "horizon:project:baremetal:compose"
    classes = ("ajax-modal",)
    icon = "plus"
    ajax = True
    

class DecomposeNode(tables.DeleteAction):
    name = "decompose"
    verbose_name = _("Decompose Node")
    classes = ("btn-danger",)
    help_text = _("Decomposed nodes are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(u"Decompose Node", u"Decompose Nodes", count)

    @staticmethod
    def action_past(count):
        return ungettext_lazy(u"Decomposed Node", u"Decomposed Nodes", count)

    def allowed(self, request, node=None):
        """Allow decompose action if node not currently being decomposed."""
        return not is_decomposing(request, node)

    def action(self, request, obj_id):
        api.valence.node_decompose(request, obj_id)
        #api.valence.test(request, "decompose node: %s" % obj_id)


class DeployOs(tables.LinkAction):
    name = "deploy"
    verbose_name = _("Deploy OS")
    url = "horizon:project:baremetal:deploy"
    classes = ("btn-confirm", "ajax-modal")
    ajax = True


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, node_id):
        print "Project: UpdateRow.get_data(%s)" % node_id
        try:
            composed_nodes = api.valence.composed_node_list(request)
                    
            for node in composed_nodes:
                if node.uuid == node_id:
                    node = untag_node_name(request, node)
                    print node
                    return node
                    
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve composed nodes.'),
                              ignore=True)
        
        return None
        

def get_os_info(node):
    template_name = 'project/baremetal/_os_status.html'

    os_name = ""
    ips = []
    state = ""
    last_error = ""
    if hasattr(node, "provision"):
        if node.provision["os_name"]:
            os_name = node.provision["os_name"]

        if len(node.provision["nics"]):
            for nic in node.provision["nics"]:
                ips += nic["ips"]
        
        if node.provision["state"]:
            state = node.provision["state"]
        
        if node.provision["last_error"]:
            last_error = node.provision["last_error"]
            
    context = {"os_name": os_name,
                "ips": ips,
                "state": state,
                "last_error": last_error}

    return template.loader.render_to_string(template_name, context)

    
def get_os_status(node):
    return node.provision["state"]


def get_memory_size(node):
    return str(node.total_memory_size_gb) + " GB"


def get_node_status(node):
    return node.status["state"].lower()
    

STATUS_DISPLAY_CHOICES = (
    ("assembling", pgettext_lazy("Current status of a composed node", u"Assembling")),
    ("assembled", pgettext_lazy("Current status of a composed node", u"Assembled")),
    ("allocating", pgettext_lazy("Current status of a composed node", u"Allocating")),
    ("allocated", pgettext_lazy("Current status of a composed node", u"Allocated")),
    ("failed", pgettext_lazy("Current status of a composed node", u"Failed"))
)


POWER_STATE_DISPLAY_CHOICES = (
    ("on", pgettext_lazy("Current power state of a composed node", u"On")),
    ("off", pgettext_lazy("Current power state of a composed node", u"Off")),
    ("poweringon", pgettext_lazy("Current power state of a composed node", u"PoweringOn")),
    ("poweringoff", pgettext_lazy("Current power state of a composed node", u"PoweringOff")),
)


OS_STATUS_DISPLAY_CHOICES = (
    ("deploying", pgettext_lazy("Current OS status of a compute node", u"Deploying")),
    ("available", pgettext_lazy("Current OS status of a compute node", u"Available")),
    ("error", pgettext_lazy("Current OS status of a compute node", u"Error"))
)


class BareMetalTable(tables.DataTable):
    POWER_STATE_CHOICES = (
        ("on", True),
        ("off", False),
        ("poweringon", True),
        ("poweringoff", True)
    )
    
    STATUS_CHOICES = (
        ("allocated", True),
        ("allocating", None),
        ("assembled", True),
        ("assembling", None),          
        ("failed", False)
    )
    
    OS_STATUS_CHOICES = (
        ("available", True),
        ("deploying", None),
        ("error", False),
        (None, True),
        ("None", True)
    )
    
    name = tables.Column("name",
                        link="horizon:project:baremetal:detail",
                        verbose_name=_("Name"))
    description = tables.Column("description",
                        verbose_name=_("Description"))
    power_state = tables.Column("power_state",
                                verbose_name=_("Power"),
                                status=True,
                                status_choices=POWER_STATE_CHOICES,
                                display_choices=POWER_STATE_DISPLAY_CHOICES)
    status = tables.Column(get_node_status,
                            verbose_name=_("Status"),
                            status=True,
                            status_choices=STATUS_CHOICES,
                            display_choices=STATUS_DISPLAY_CHOICES)
    os_status = tables.Column(get_os_status,
                            status=True,   
                            empty_value="None",
                            status_choices=OS_STATUS_CHOICES,
                            display_choices=OS_STATUS_DISPLAY_CHOICES,
                            verbose_name=_("OS Status"))
    os_info = tables.Column(get_os_info,
                            verbose_name=_("OS Info"),
                            attrs={"data-type":"ip"})
    cpu_count = tables.Column("total_cpu_count",
                            verbose_name=_("CPU Count"))
    memory_size = tables.Column(get_memory_size,
                                verbose_name=_("Memory"),
                                attrs={"data-type":"size"})
    nvme_count = tables.Column("total_nvme_drives",
                                verbose_name=_("NVMe Count"))

    class Meta(object):
        name = "baremetal"
        verbose_name = _("Bare Metal")
        status_columns = ["power_state", "status", "os_status"]
        table_actions = (ComposeNode, DecomposeNode)
        row_class = UpdateRow
        row_actions = (DeployOs, DecomposeNode)
        