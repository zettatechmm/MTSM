# -*- coding: utf-8 -*-

from typing import Dict, List
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang
from odoo.tools.float_utils import float_compare, float_round
import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_studio_branch = fields.Many2one("x_branches", string="Branch", default=lambda self: self.env.user.x_studio_default_branch.id)
    
    def _get_default_purchase_journal(self):
        res = self.env['account.journal'].search([('type' , '=', 'purchase'), ('company_id', '=', self.env.company.id)], limit=1)
        return res
    
    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res.update({
                    'x_studio_branch': self.x_studio_branch.id,
                    'journal_id': self._get_default_purchase_journal().id
                    })    
        return res
