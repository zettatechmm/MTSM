# -*- coding: utf-8 -*-
from odoo import fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_confirmation_values(self):
        res = super()._prepare_confirmation_values()
        res.update({'date_order': self.date_order})
        return res