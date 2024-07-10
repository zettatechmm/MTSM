
from typing import Dict, List
from odoo import api, fields, models, SUPERUSER_ID, _

# class PurchaseOrder(models.Model):
#     _inherit = "purchase.order"

#     @api.onchange('x_studio_branch')
#     def _onchange_branch(self):
#         super()._onchange_branch()
#         if self.x_studio_branch:     
#             for line in self.order_line:                  
#                 line.branch_id = self.x_studio_branch.id

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    branch_id = fields.Many2one("x_branches", string="Branch", related="order_id.x_studio_branch", store=True)
    
    # @api.depends('branch_id')
    # def _compute_branch(self):
    #     for line in self:
    #         if line.order_id.x_studio_branch:
    #             line.branch_id = line.order_id.mapped('x_studio_branch').id
    #         else:
    #             line.branch_id = False
    
    # @api.depends('product_id', 'order_id.partner_id', 'branch_id')
    # def _compute_analytic_distribution(self):
    #     for line in self:
    #         if not line.display_type:
    #             distribution = self.env['account.analytic.distribution.model']._get_distribution({
    #                 "product_id": line.product_id.id,
    #                 "product_categ_id": line.product_id.categ_id.id,
    #                 "partner_id": line.order_id.partner_id.id,
    #                 "partner_category_id": line.order_id.partner_id.category_id.ids,
    #                 "branch_id":line.branch_id.id,
    #                 "company_id": line.company_id.id,
    #             })
    #             line.analytic_distribution = distribution and line.analytic_distribution and {**distribution,**line.analytic_distribution} or distribution or line.analytic_distribution