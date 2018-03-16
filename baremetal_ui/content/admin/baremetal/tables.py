import logging

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from django.utils.translation import pgettext_lazy

from django import template

from openstack_dashboard import api

from horizon import exceptions
from horizon import tables

LOG = logging.getLogger(__name__)


def is_deleting(request, node):
    # To do: Get node status
    return False


class AddNode(tables.LinkAction):
    """Compose node."""
    name = "compose"
    verbose_name = _("Add Node")
    url = "horizon:admin:baremetal:compose"
    classes = ("ajax-modal", "btn-launch")
    icon = "plus"
    ajax = True

    
class DeleteNode(tables.DeleteAction):
    """Decompose Node."""
    name = "delete"
    verbose_name = _("Delete Node")
    classes = ("btn-danger",)
    help_text = _("Deleted nodes are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(u"Delete Node", u"Delete Nodes", count)

    @staticmethod
    def action_past(count):
        return ungettext_lazy(u"Deleted Node", u"Deleted Nodes", count)

    def allowed(self, request, node=None):
        """Allow delete action if node not currently being deleted."""
        return not is_deleting(request, node)

    def action(self, request, obj_id):
        api.valence.node_decompose(request, obj_id)
        #api.valence.test(request, "delete node: %s" % obj_id)
        
        # Delete nova-compute
        srv_list = api.valence.compute_service_list(request, "nova-compute")
        for srv in srv_list:
            if srv.host == "ubuntu":
                api.valence.compute_service_delete(request, srv.id)
        
        
class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, node_id):
        print "Admin: UpdateRow.get_data(%s)" % node_id
        try:            
            composed_nodes = api.valence.composed_node_list(request)
            
            for node in composed_nodes:
                if node.uuid == node_id:
                    print node
                    return node
                    
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve composed nodes.'),
                              ignore=True)
        
        return None

        
def get_os_info(node):
    print "get_os_status()"
    template_name = 'admin/baremetal/_os_status.html'

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
    return node.status["state"]


def get_role(node):
    desc = node.description.replace("[", "")
    return desc[0:desc.rindex("]")]


STATUS_DISPLAY_CHOICES = (
    ("assembling", pgettext_lazy("Current status of a compute node", u"Assembling")),
    ("assembled", pgettext_lazy("Current status of a compute node", u"Assembled")),
    ("allocating", pgettext_lazy("Current status of a compute node", u"Allocating")),
    ("allocated", pgettext_lazy("Current status of a compute node", u"Allocated")),
    ("failed", pgettext_lazy("Current status of a compute node", u"Failed"))
)


POWER_STATE_DISPLAY_CHOICES = (
    ("on", pgettext_lazy("Current power state of a compute node", u"On")),
    ("off", pgettext_lazy("Current power state of a compute node", u"Off")),
    ("poweringon", pgettext_lazy("Current power state of a compute node", u"PoweringOn")),
    ("poweringoff", pgettext_lazy("Current power state of a compute node", u"PoweringOff")),
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
        ("allocating", None),
        ("allocated", True),
        ("assembling", None),
        ("assembled", True),    
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
                        verbose_name=_("Name"))  
    role = tables.Column(get_role,
                        verbose_name=_("OpenStack Role"))
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


    class Meta(object):
        name = "baremetal"
        verbose_name = _("Bare Metal")
        status_columns = ["power_state", "status", "os_status"]
        table_actions = (AddNode, DeleteNode)
        row_class = UpdateRow
        row_actions = (DeleteNode,)

        