# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'baremetal'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'project'
# The slug of the panel group the PANEL is associated with.
PANEL_GROUP = 'compute'

# Python panel class of the PANEL to be added.
ADD_PANEL = 'openstack_dashboard.dashboards.project.baremetal.panel.Baremetal'
#REMOVE_PANEL = True