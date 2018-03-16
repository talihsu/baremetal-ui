#!/bin/bash
set -x


cp -rf ../baremetal_ui/content/project/baremetal /usr/share/openstack-dashboard/openstack_dashboard/dashboards/project/
cp -rf ../baremetal_ui/content/admin/baremetal /usr/share/openstack-dashboard/openstack_dashboard/dashboards/admin/
cp -rf ../baremetal_ui/api/* /usr/share/openstack-dashboard/openstack_dashboard/api
cp -rf ../baremetal_ui/enabled/* /usr/share/openstack-dashboard/openstack_dashboard/enabled

service apache2 restart
