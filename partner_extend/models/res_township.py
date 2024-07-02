from odoo import models, fields, api, _ 
from odoo.exceptions import AccessError, UserError, ValidationError

class ResTownship(models.Model):
    _name = "res.township"
    _description = 'Township'

    name = fields.Char(string='Name', required=True)
    state_id = fields.Many2one('res.country.state', string='State')
    code = fields.Char('Code')
    number_of_digits = fields.Integer('Number of Digits',default=4)
    next_number = fields.Integer('Next Number',default=1)

    _sql_constraints = [('unique_code', 'unique(code)', 'Cannot create duplicate Code!')]

    def get_reference(self):
        for rec in self:
            next_number = rec.next_number or 1
            code = rec.code or ''
            if not code:
                raise ValidationError('%s does not have township code to generate.'%(rec.name))
            ref = code+'{:04d}'.format(next_number)
            rec.next_number = next_number+1
            return ref
