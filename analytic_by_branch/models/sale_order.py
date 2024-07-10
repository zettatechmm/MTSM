from typing import Dict, List
from odoo import api, fields, models, SUPERUSER_ID, _

# class SaleOrder(models.Model):
#     _inherit = "sale.order"
    
#     @api.onchange('order_line', 'partner_id', 'partner_shipping_id')
#     def onchange_order_line(self):
#         super().onchange_order_line()
#         for line in self.order_line:
#             if line.order_id.x_studio_branch:                    
#                     line.branch_id = self.x_studio_branch.id

#     # @api.onchange('order_line','order_line.branch_id')
#     # def _onchange_order_line(self):
#     #     for line in self:
#     #         if line.order_id.x_studio_branch:                    
#     #                 line.branch_id = self.x_studio_branch.id
            
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    branch_id = fields.Many2one("x_branches", string="Branch", related="order_id.x_studio_branch", store=True)
    
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