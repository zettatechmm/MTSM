from collections import defaultdict
from odoo import api, fields, models


class Partner(models.Model):
    _inherit = "res.partner"


    def _prepare_display_address(self, without_company=False):
        # get the information that will be injected into the display format
        # get the address format
        result = super()._prepare_display_address(without_company)
        res_list = list(result)
        if res_list:
            res_list[0] = "%(street)s\n%(street2)s\n%(city)s %(state_name)s %(zip)s\n%(country_name)s"
        return tuple(res_list)