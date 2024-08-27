from odoo import api, Command, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    consignment_no = fields.Char(string="Consignment No", copy=False)
    x_studio_branch = fields.Many2one("x_branches", default=lambda self: self.env.user.x_studio_default_branch.id)
    warehouse_id = fields.Many2one(
                    'stock.warehouse', string='Warehouse', required=True,
                    compute='_compute_warehouse_id', store=True, readonly=False, precompute=True,
                    check_company=True, domain="['|', ('x_studio_branch', '=', False), ('x_studio_branch', '=', x_studio_branch)]")
    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer", required=True, 
                                change_default=True, index=True, tracking=1,check_company=True, 
                                domain="['|', ('x_studio_branch', '=', False), ('x_studio_branch', '=', x_studio_branch)]")
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'company_id' in vals:
                self = self.with_company(vals['company_id'])
            if 'x_studio_branch' in vals and vals['x_studio_branch']:
                branch = self.env['x_branches'].browse(vals['x_studio_branch'])
                if branch:
                    if vals.get('name', _("New")) == _("New"):
                        seq_date = fields.Datetime.context_timestamp(
                            self, fields.Datetime.to_datetime(vals['date_order'])
                        ) if 'date_order' in vals else None
                        vals['name'] = self.env['ir.sequence'].next_by_code_by_branch('sale.order.branch', sequence_date=seq_date, branch_id=branch.id) or _("New")
        return super().create(vals_list)
    
        
    #add note SO to DO
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            for picking in order.picking_ids:
                picking.note = order.note
        return res
    
    # def action_confirm(self):
    #     super().action_confirm()
    #     for order in self:
    #         if order.x_studio_branch and 'consignment' in list(map(str.lower, order.tag_ids.mapped('name'))):
    #             order.consignment_no = self.env['ir.sequence'].next_by_code_by_branch('so.consignment.branch', branch_id=order.x_studio_branch.id)

    def action_confirm(self):
        super().action_confirm()
        for order in self:
            if 'consignment' in list(map(str.lower, order.tag_ids.mapped('name'))):
                order.consignment_no = self.env['ir.sequence'].next_by_code('so.consi.sequence')
            else:
                order.consignment_no = False

            
    def _get_warehouse(self, branch_id):
        res = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id), ('x_studio_branch', '=', branch_id)], limit=1)
        return res
    
    @api.onchange('x_studio_branch')
    def _onchange_branch(self):
        if self.x_studio_branch:       
            self.warehouse_id = self._get_warehouse(self.x_studio_branch.id).id
    
    def _get_default_journal(self):
        res = self.env['account.journal'].search([('type' , '=', 'sale'), ('company_id', '=', self.env.company.id), ('x_studio_branch', '=', self.x_studio_branch.id)], limit=1)
        return res
    
    def _prepare_invoice(self):
        res = super()._prepare_invoice() 
        res.update({
                    'x_studio_branch': self.x_studio_branch.id,
                    'journal_id': self._get_default_journal().id,
                    'x_studio_ordered_by': self.x_studio_ordered_by_1.id,
                    'x_studio_salespersons': self.x_studio_salespersons.ids,
                    'consignment_no': self.consignment_no})
        return res   
    
    