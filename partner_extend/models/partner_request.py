from odoo import models, fields, api, _


class PartnerRequest(models.Model):
    _name = "partner.request"
    _description = 'Partner Request'
    _inherit = ['mail.thread','mail.activity.mixin',]

    def _default_category(self):
        return self.env['res.partner.category'].browse(self._context.get('category_id'))

    is_partner_request = fields.Boolean(default=False,compute='_compute_is_partner_request')
    state = fields.Selection(string='Status',
                            selection=[('submit', 'Submitted'), ('approved', 'Approved')],
                            default='submit',tracking=1)
    parent_id = fields.Many2one('res.partner', string='Related Company', index=True, copy=False)
    name = fields.Char(index=True, default_export_compatible=True, copy=False,tracking=1)
    website = fields.Char('Website Link')
    facebook = fields.Char('Facebook Link')
    title = fields.Many2one('res.partner.title')
    function = fields.Char(string='Job Position')
    is_rubber = fields.Boolean('Rubber')
    is_submitted = fields.Boolean('Is Submitted', copy=False)
    township_id = fields.Many2one('res.township',
                                  string='Township',
                                  ondelete='restrict',
                                  domain="[('state_id', '=?', state_id)]")

    city = fields.Char(related='city_village_id.name', string='City Char')
    city_village_id = fields.Many2one('city.village',
                                      string='City/Village',
                                      domain="[('township_id', '=?', township_id)]",
                                      ondelete='restrict')
    vat = fields.Char(string='Tax ID', index=True,
                      help="The Tax Identification Number. Values here will be validated based on the country format. You can use '/' to indicate that the partner is not subject to tax.")
    
    crm_tag_ids = fields.Many2many('crm.tag', column1='partner_id',
                                   column2='crm_tag_id', string='CRM Tags', copy=False)
    
    category_id = fields.Many2many('res.partner.category', column1='partner_id',
                                   column2='category_id', string='Tags', default=_default_category, copy=False)
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    country_code = fields.Char(related='country_id.code', string="Country Code")
    email = fields.Char('Email', copy=False)
    company_id = fields.Many2one('res.company', 'Company', index=True)
    phone = fields.Char(string='Viber Phone',unaccent=False, copy=False)
    mobile = fields.Char(unaccent=False, copy=False)
    is_company = fields.Boolean(string='Is a Company', default=False,
                                help="Check if the contact is a company, otherwise it is a person")
    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'), ('company', 'Company')],
                                    compute='_compute_company_type', inverse='_write_company_type')
    company_name = fields.Char('Company Name')
    type = fields.Selection(
        [('contact', 'Contact'),
         ('invoice', 'Invoice Address'),
         ('delivery', 'Delivery Address'),
         ('other', 'Other Address'),
         ], string='Address Type',
        default='contact',
        help="- Contact: Use this to organize the contact details of employees of a given company (e.g. CEO, CFO, ...).\n"
             "- Invoice Address: Preferred address for all invoices. Selected by default when you invoice an order that belongs to this company.\n"
             "- Delivery Address: Preferred address for all deliveries. Selected by default when you deliver an order that belongs to this company.\n"
             "- Other: Other address for the company (e.g. subsidiary, ...)")
    birthday = fields.Date(string='Birthday')
    image = fields.Image("Image", store=True, copy=False, attachment=True)
    comment = fields.Html(string='Notes')
    industry_id = fields.Many2one('res.partner.industry',string='Industry')
    payment_term_id = fields.Many2one('account.payment.term',string='Payment Term')
    pricelist_id = fields.Many2one('product.pricelist',string='Pricelist')

    def _compute_is_partner_request(self):
        for partner_request in self:
            partner_request.is_partner_request = True

    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            partner.company_type = 'company' if partner.is_company else 'person'

    def _write_company_type(self):
        for partner in self:
            partner.is_company = partner.company_type == 'company'

    @api.onchange('company_type')
    def onchange_company_type(self):
        self.is_company = (self.company_type == 'company')

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id.country_id and self.country_id != self.state_id.country_id:
            self.country_id = self.state_id.country_id

    def submit_new_customer(self):
        for partner in self:
            partner.is_submitted = True
            partner.state = 'approved'
            partner_vals = partner.env['res.partner'].create(
                {
                    "name": partner.name,
                    "company_type": partner.company_type,
                    "company_name": partner.company_name,
                    "type": partner.type,
                    "parent_id": partner.parent_id.id,
                    "street": partner.street,
                    "street2": partner.street2,
                    "zip": partner.zip,
                    "city_village_id": partner.city_village_id.id,
                    "township_id": partner.township_id.id,
                    "state_id": partner.state_id.id,
                    "country_id": partner.country_id.id,
                    "vat": partner.vat,
                    "is_rubber": partner.is_rubber,
                    "function": partner.function,
                    "phone": partner.phone,
                    "mobile": partner.mobile,
                    "birthday": partner.birthday,
                    "email": partner.email,
                    "website": partner.website,
                    "facebook": partner.facebook,
                    "title": partner.title.id,
                    "category_id": partner.category_id.ids,
                    "crm_tag_ids": partner.crm_tag_ids.ids,
                    "comment": partner.comment,
                    "image_1920": partner.image,
                    'industry_id':partner.industry_id.id,
                    "property_product_pricelist":partner.pricelist_id.id,
                    "property_payment_term_id":partner.payment_term_id.id,
                }
            )
            return partner_vals
