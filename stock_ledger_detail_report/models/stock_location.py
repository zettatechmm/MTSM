from odoo import api, fields, models

class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    wh_name = fields.Char(string='Warehouse', compute="_get_warehouse_name")
    
    def _get_warehouse_name(self):
        for rec in self:
            rec.wh_name = rec.warehouse_id.name
