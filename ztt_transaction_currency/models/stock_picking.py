from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    currency_rate = fields.Float('Currency Rate',default=1)