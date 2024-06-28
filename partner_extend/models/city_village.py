from odoo import models, fields, api, _


class CityVillage(models.Model):
    _name = "city.village"
    _description = 'City Village'

    name = fields.Char(string='Name', required=True)
    township_id = fields.Many2one('res.township', string='Township')
