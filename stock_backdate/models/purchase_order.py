# -*- coding: utf-8 -*-
from odoo import fields, models

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_approve(self, force=False):
        super().button_approve(force=False)
        self.write({'date_approve': self.date_order})
        return {}