from odoo import models, api

class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        vals = super(StockRule, self)._push_prepare_move_copy_values(move_to_copy, new_date)
        vals.update({'state': 'draft'})
        return vals