from odoo import models, fields

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    township_id = fields.Many2one('res.township', string='Township', related='partner_id.township_id')
    state_id = fields.Many2one('res.country.state', string='State', related='partner_id.state_id')
    categ_ids = fields.Many2many('res.partner.category', string='Tags', related='partner_id.category_id')
