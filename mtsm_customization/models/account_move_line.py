from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError
 
class AccountMoveLine(models.Model): 
    _inherit = "account.move.line"

    customer_name = fields.Char(string="Customer Name",related="move_id.partner_id.name")
    customer_code = fields.Char(string="Customer Code",related="move_id.partner_id.ref")

    product_name = fields.Char(string="Product Name",related="product_id.name")
    product_code = fields.Char(string="Product Code",related="product_id.default_code")