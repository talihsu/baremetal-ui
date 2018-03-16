from django.utils.translation import ugettext_lazy as _

import horizon


class Baremetal(horizon.Panel):
    name = _("Bare Metal")
    slug = "baremetal"


