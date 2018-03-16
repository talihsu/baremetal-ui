from horizon import views
from horizon import exceptions
from horizon import tables
from horizon import forms
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy

from openstack_dashboard import api
from openstack_dashboard.dashboards.admin.baremetal \
    import tables as baremetal_tables
from openstack_dashboard.dashboards.admin.baremetal \
    import forms as baremetal_forms
    
class IndexView(tables.DataTableView):
    table_class = baremetal_tables.BareMetalTable
    template_name = 'admin/baremetal/index.html'
    page_title = _("Bare Metal")

    def get_data(self):
        """Get composed nodes from Valence."""
        try:
            composed_nodes = api.valence.composed_node_list(self.request)
            
            # Only show the nodes which are deployed as OpenStack nodes
            # description = [Compute] | [Storage] | [Network]
            _nodes = []
            for node in composed_nodes:
                if (node.description.startswith("[Compute]") or 
                    node.description.startswith("[Storage]") or
                    node.description.startswith("[Network]")):
                    _nodes.append(node)
                    
            composed_nodes = _nodes
            print composed_nodes

        except Exception:
            composed_nodes = []
            exceptions.handle(self.request,
                              _('Unable to retrieve composed nodes.'))
                              
        return composed_nodes
        
class ComposeView(forms.ModalFormView):
    form_class = baremetal_forms.AddNode
    template_name = 'admin/baremetal/compose.html'
    success_url = reverse_lazy('horizon:admin:baremetal:index')
    page_title = _("Add Node")
