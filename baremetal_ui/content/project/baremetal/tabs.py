from django.utils.translation import ugettext_lazy as _

from horizon import tabs

def untag_node_name(request, node):
    node.name = node.name.replace("-" + request.user.username + \
                                "-" + request.user.tenant_id, "")
    return node
    
class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "project/baremetal/_detail_overview.html"

    def get_context_data(self, request):
        node = self.tab_group.kwargs['node']
        
        return {"node": untag_node_name(request, node)}


class BaremetalDetailTabs(tabs.TabGroup):
    slug = "baremetal_details"
    tabs = (OverviewTab,)