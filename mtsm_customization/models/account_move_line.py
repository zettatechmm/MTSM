from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError
 
class AccountMoveLine(models.Model): 
    _inherit = "account.move.line"

    customer_name = fields.Char(string="Customer Name",related="move_id.partner_id.name")
    customer_code = fields.Char(string="Customer Code",related="move_id.partner_id.ref")

    product_name = fields.Char(string="Product Name",related="product_id.name")
    product_code = fields.Char(string="Product Code",related="product_id.default_code") 

    return_quantity = fields.Float(string="Quantity", compute="_compute_return_quantity")
    return_full_amount = fields.Float(string="Full Amount", compute="_compute_return_full_amount")
    return_price_total = fields.Float(string="Total Amount", compute="_compute_return_price_total")

    @api.depends('quantity','move_type')
    def _compute_return_quantity(self):
        for rec in self:
            if rec.move_type == 'out_refund':
             rec.return_quantity = -1 * rec.quantity if rec.quantity else 0.0
            else:
               rec.return_quantity = rec.quantity

    @api.depends('quantity','price_unit') 
    def _compute_return_full_amount(self):
        for rec in self:
            rec.return_full_amount = rec.return_quantity * rec.price_unit or 0.0

    @api.depends('price_total','move_type')
    def _compute_return_price_total(self):
        for rec in self:
            if rec.move_type == 'out_refund':
             rec.return_price_total = -1 * rec.price_total if rec.price_total else 0.0
            else:
               rec.return_price_total = rec.price_total