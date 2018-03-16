from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.project.baremetal import views

NODES = r'^(?P<node_id>[^/]+)/%s$'

urlpatterns = patterns(
    'openstack_dashboard.dashboards.project.baremetal.views',

    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<node_id>[^/]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^compose$', views.ComposeView.as_view(), name='compose'),
    url(NODES % 'deploy', views.DeployView.as_view(), name='deploy'),
)
