from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = 'stock.picking'

    def if_split(self, vals):
        """
        condition to check whether to split picking contrast to odoo default merge
        """
        location_id = self.env['stock.location'].sudo().search([('id', '=', vals.get('location_dest_id'))])
        # defaults = self.default_get(['name', 'picking_type_id'])
        # picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id')))
        if location_id.usage == 'transit':
            return True
        return False

    @api.model
    def create(self, vals):
        """
        use `procurement.group` to split instead of merge
        """
        defaults = self.default_get(['name', 'picking_type_id'])
        picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id')))
        if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id', defaults.get('picking_type_id')):
            if picking_type.sequence_id:
                vals['name'] = picking_type.sequence_id.next_by_id()

        # As the on_change in one2many list is WIP, we will overwrite the locations on the stock moves here
        # As it is a create the format will be a list of (0, 0, dict)
        moves = vals.get('move_lines', []) + vals.get('move_ids', [])+ vals.get('move_ids_without_package', [])
        if moves and vals.get('location_id') and vals.get('location_dest_id'):
            for move in moves:
                if len(move) == 3 and move[0] == 0:
                    move[2]['location_id'] = vals['location_id']
                    move[2]['location_dest_id'] = vals['location_dest_id']
                    # When creating a new picking, a move can have no `company_id` (create before
                    # picking type was defined) or a different `company_id` (the picking type was
                    # changed for an another company picking type after the move was created).
                    # So, we define the `company_id` in one of these cases.
                    picking_type = self.env['stock.picking.type'].browse(vals['picking_type_id'])
                    if 'picking_type_id' not in move[2] or move[2]['picking_type_id'] != picking_type.id:
                        move[2]['picking_type_id'] = picking_type.id
                        move[2]['company_id'] = picking_type.company_id.id
        # make sure to write `schedule_date` *after* the `stock.move` creation in
        # order to get a determinist execution of `_set_scheduled_date`
        scheduled_date = vals.pop('scheduled_date', False)

        # custom code
        if self.if_split(vals):
            if not moves and 'locatione_dest_id' in vals and self.location_id != vals.get('location_dest_id'):
                raise UserError(_('Please select product.'))
            group_id = self.env['procurement.group'].create({'name': vals['name']})
            vals['group_id'] = group_id.id
            for move in moves:
                if len(move) == 3 and move[0] == 0:
                    move[2]['group_id'] = group_id.id

        res = super(Picking, self).create(vals)
        if scheduled_date:
            res.with_context(mail_notrack=True).write({'scheduled_date': scheduled_date})

        # custom code
        if self.if_split(vals):
            self = self.with_context(default_picking_id=self.id)

        # set partner as follower
        if vals.get('partner_id'):
            for picking in res.filtered(lambda p: p.location_id.usage == 'supplier' or p.location_dest_id.usage == 'customer'):
                picking.message_subscribe([vals.get('partner_id')])

        return res
