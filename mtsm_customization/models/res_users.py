from odoo import models, fields, api

class Users(models.Model):
    _inherit = 'res.users'
    
    @api.onchange('x_studio_allowed_branches')
    def _clear_rule_cache(self):
        self.env['ir.rule'].clear_caches()
        
    def _get_default_warehouse_id(self):
        # !!! Any change to the following search domain should probably
        # be also applied in sale_stock/models/sale_order.py/_init_column.
        return self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id), ('x_studio_branch', '=', self.env.user.x_studio_default_branch.id)], limit=1)