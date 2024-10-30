from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError
 
class AccountMoveLine(models.Model): 
    _inherit = "account.move.line"

    customer_name = fields.Char(string="Customer Name",related="move_id.partner_id.name")
    customer_code = fields.Char(string="Customer Code",related="move_id.partner_id.ref")

    product_name = fields.Char(string="Product Name",related="product_id.name")
    product_code = fields.Char(string="Product Code",related="product_id.default_code") 

    return_quantity = fields.Float(string="Quantity", compute="_compute_return_quantity")
    return_unit_price = fields.Float(string="Unit Price", compute="_compute_return_unit_price")
    return_full_amount = fields.Float(strin="Full Amount", compute="_compute_return_full_amount")

    @api.depends('quantity')
    def _compute_return_quantity(self):
        for rec in self:
            if rec.move_type == 'out_refund':
             rec.return_quantity = - rec.quantity
            else:
               rec.return_quantity = rec.quantity

    @api.depends('price_unit')
    def _compute_return_unit_price(self):
        for rec in self:
            if rec.move_type == 'out_refund':
             rec.return_unit_price = - rec.price_unit
            else:
               rec.return_unit_price = rec.price_unit

    @api.depends('quantity','price_unit')
    def _compute_return_full_amount(self):
        for rec in self:
            rec.return_full_amount = rec.return_quantity * rec.return_unit_price or 0.0