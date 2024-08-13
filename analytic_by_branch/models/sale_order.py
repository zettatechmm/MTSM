from typing import Dict, List
from odoo import api, fields, models, SUPERUSER_ID, _
            
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    branch_id = fields.Many2one("x_branches", string="Branch", related="order_id.x_studio_branch", store=True)
    
    def _get_protected_fields(self):
        """ Give the fields that should not be modified on a locked SO.

        :returns: list of field names
        :rtype: list
        """
        return [
            'product_id', 'name', 'price_unit', 'product_uom', 'product_uom_qty',
            'tax_id'
        ]
    
    @api.depends('order_id.partner_id', 'product_id', 'branch_id')
    def _compute_analytic_distribution(self):
        for line in self:
            if not line.display_type:
                distribution = line.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": line.product_id.id,
                    "product_categ_id": line.product_id.categ_id.id,
                    "partner_id": line.order_id.partner_id.id,
                    "partner_category_id": line.order_id.partner_id.category_id.ids,
                    "branch_id":line.branch_id.id,
                    "company_id": line.company_id.id,
                })
                line.analytic_distribution = distribution and line.analytic_distribution and {**distribution,**line.analytic_distribution} or distribution or line.analytic_distribution
                
                
    def update_analytic_distribution(self):
        lines = self.env['sale.order.line'].search([('analytic_distribution', '=', False)])
        for line in lines:
            distribution = line.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": line.product_id.id,
                    "product_categ_id": line.product_id.categ_id.id,
                    "partner_id": line.order_id.partner_id.id,
                    "partner_category_id": line.order_id.partner_id.category_id.ids,
                    "branch_id":line.branch_id.id,
                    "company_id": line.company_id.id,
                })
            line.analytic_distribution = distribution and line.analytic_distribution and {**distribution,**line.analytic_distribution} or distribution or line.analytic_distribution
