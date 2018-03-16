from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.admin.baremetal import views


urlpatterns = patterns(
    'openstack_dashboard.dashboards.admin.baremetal.views',
    
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^compose$', views.ComposeView.as_view(), name='compose')
)
