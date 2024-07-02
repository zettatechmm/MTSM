from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
import re


class Partner(models.Model):
    _inherit = 'res.partner'

    def _get_complete_name(self):
        return super()._get_complete_name()

    @api.depends('complete_name', 'ref', 'email', 'vat', 'state_id', 'country_id', 'commercial_company_name')
    @api.depends_context('show_address', 'partner_show_db_id', 'address_inline', 'show_email', 'show_vat', 'lang')
    def _compute_display_name(self):
        for partner in self:
            name = partner.with_context({'lang': self.env.lang})._get_complete_name()
            if partner._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = re.sub(r'\s+\n', '\n', name)
            if partner._context.get('partner_show_db_id'):
                name = f"{name} ({partner.id})"
            if partner._context.get('address_inline'):
                splitted_names = name.split("\n")
                name = ", ".join([n for n in splitted_names if n.strip()])
            if partner._context.get('show_email') and partner.email:
                name = f"{name} <{partner.email}>"
            if partner._context.get('show_vat') and partner.vat:
                name = f"{name} ‒ {partner.vat}"
            if partner.ref:
                name='['+partner.ref+'] '+name
            partner.display_name = name.strip()

    is_rubber = fields.Boolean('Rubber')
    township_id = fields.Many2one('res.township',
                                  string='Township',
                                  ondelete='restrict',
                                  domain="[('state_id', '=?', state_id)]")

    city = fields.Char(related='city_village_id.name', string='City Char')
    city_village_id = fields.Many2one('city.village',
                                      string='City/Village',
                                      domain="[('township_id', '=?', township_id)]",
                                      ondelete='restrict')
    facebook = fields.Char('Facebook Link')
    crm_tag_ids = fields.Many2many('crm.tag', column1='partnerr_id',
                                   column2='crmm_tag_id', string='CRM Tags', copy=False)
    phone = fields.Char(string='Viber Phone',unaccent=False)
    mobile = fields.Char(unaccent=False,required=True)

    def action_get_reference(self):
        for rec in self:
            if not rec.township_id:
                raise ValidationError("%s does not have township to generate reference code."%(rec.name))
            rec.ref=rec.township_id.get_reference()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
          township_id=vals.get('township_id',False)
          if 'township_id' in vals and township_id:
            reference = self.env['res.township'].browse(int(township_id)).get_reference()
            vals['ref'] = reference

        return super().create(vals_list)

    def write(self, values):
        for rec in self:
            if 'township_id' in values:
                township_id=values.get('township_id',False)
                if 'township_id' in values and township_id and int(township_id)!=rec.township_id.id:
                    reference = self.env['res.township'].browse(int(township_id)).get_reference()
                    values['ref']=reference
        return super().write(values)