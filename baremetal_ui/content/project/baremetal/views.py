from horizon import views
from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon import tabs
from horizon.utils import memoized
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.baremetal \
    import tables as baremetal_tables
from openstack_dashboard.dashboards.project.baremetal \
    import forms as baremetal_forms
from openstack_dashboard.dashboards.project.baremetal \
    import tabs as baremetal_tabs   

def untag_node_name(request, node):
    node.name = node.name.replace("-" + request.user.username + \
                                "-" + request.user.tenant_id, "")
    return node
                             
def tag_node_name(request, node):
    node.name += "-" + request.user.username + \
                "-" + request.user.tenant_id
    return node
                             
class IndexView(tables.DataTableView):
    table_class = baremetal_tables.BareMetalTable
    template_name = 'project/baremetal/index.html'
    page_title = _("Bare Metal")

    def get_data(self):
        """Get composed nodes from Valence."""
        try:
            composed_nodes = api.valence.composed_node_list(self.request)
            
            # Filter out the nodes which are deployed as OpenStack nodes
            # and not for current tenant
            # 1. description = [Compute] | [Storage] | [Network]
            # 2. "name-username-tenant_id"
            tag = "-" + self.request.user.username + \
                "-" + self.request.user.tenant_id
            _nodes = []
            for node in composed_nodes:
                if (not node.description.startswith("[Compute]") and
                    not node.description.startswith("[Storage]") and
                    not node.description.startswith("[Network]") and
                    node.name.endswith(tag)):
                    node = untag_node_name(self.request, node)
                    _nodes.append(node)
                    
            composed_nodes = _nodes
            print composed_nodes

        except Exception:
            composed_nodes = []
            exceptions.handle(self.request,
                              _('Unable to retrieve composed nodes.'))
                              
        return composed_nodes
        
class ComposeView(forms.ModalFormView):
    form_class = baremetal_forms.ComposeNode
    template_name = 'project/baremetal/compose.html'
    success_url = reverse_lazy('horizon:project:baremetal:index')
    page_title = _("Compose Node")
    
class DeployView(forms.ModalFormView):
    form_class = baremetal_forms.DeployOs
    template_name = 'project/baremetal/deploy.html'
    modal_header = _("Deploy OS")
    form_id = "deploy_os_form"
    submit_label = _("Deploy OS")
    submit_url = "horizon:project:baremetal:deploy"
    success_url = reverse_lazy('horizon:project:baremetal:index')   

    def get_initial(self):
        return {"node_id": self.kwargs["node_id"]}
        
    def get_context_data(self, **kwargs):
        context = super(DeployView, self).get_context_data(**kwargs)
        context['node_id'] = self.kwargs['node_id']
        args = (self.kwargs['node_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        return context

class DetailView(tabs.TabView):
    tab_group_class = baremetal_tabs.BaremetalDetailTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ node.name }}"
    
    @staticmethod
    def get_redirect_url():
        return reverse_lazy('horizon:project:baremetal:index')

    @memoized.memoized_method
    def get_data(self):
        try:
            node = api.valence.composed_node_get(self.request, self.kwargs['node_id'])            
            return untag_node_name(self.request, node)

        except Exception as e:
            exceptions.handle(self.request,
                              _('Unable to retrieve composed node details.'),
                              redirect=self.get_redirect_url())

    def get_tabs(self, request, *args, **kwargs):
        node = self.get_data()
        return self.tab_group_class(request, node=node, **kwargs)
        
    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        node = self.get_data()

        context["node"] = node
        context["url"] = self.get_redirect_url()
        table = baremetal_tables.BareMetalTable(self.request)        
        context["actions"] = table.render_row_actions(node)
        
        return context