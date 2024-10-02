from odoo import api, fields, models


class WarehouseReportHelper(models.TransientModel):
    _name = 'stock.report.helper'
    _description = "Strock Report Helper"

    start_date = fields.Datetime()
    end_date = fields.Datetime()
    location_id = fields.Many2one('stock.location')
    product_id = fields.Many2one('product.product')

    def get_moves(self, src_location_ids, dest_location_ids):
        domain = [
            ('product_id', '=', self.product_id.id), 
            ('date', '>', self.start_date), 
            ('date', '<', self.end_date), 
            ('state', '=', 'done')
        ]
        if src_location_ids:
            domain.append(('location_id', 'in', src_location_ids.ids))
        if dest_location_ids:
            domain.append(('location_dest_id', 'in', dest_location_ids.ids))
        return self.env['stock.move.line'].search(domain)

    def get_total_in(self):
        total = 0
        for loc in self.location_id:
            src = None
            dest = loc
            moves = self.get_moves(src, dest)
            total += sum(moves.mapped('quantity'))
        return total

    def get_total_out(self):
        total = 0
        for loc in self.location_id:
            src = loc
            dest = None
            moves = self.get_moves(src, dest)
            total += sum(moves.mapped('quantity'))
        return total

    def get_receiving(self):
        total = 0
        for loc in self.location_id:
            src = self.env['stock.location'].search([('usage', '=', 'supplier')])
            dest = loc
            moves = self.get_moves(src, dest)
            total += sum(moves.mapped('quantity'))
        return total

    def get_transfer_in(self):
        total = 0
        for loc in self.location_id:            
            #src = self.warehouse_id.id
            #(move.location_id.id in transit_loc.ids or move.location_id.id in internal_loc.ids) and move.location_dest_id.id == helper.warehouse_id.lot_stock_id.id:
            transit_internal_loc = self.env['stock.location'].search(['|',('usage', '=', 'transit'),('usage', '=', 'internal')])
            domain = [
                ('product_id', '=', self.product_id.id), 
                ('date', '>', self.start_date), 
                ('date', '<', self.end_date), 
                ('state', '=', 'done'),
                ('location_dest_id', 'in', loc.ids),
                '|',
                ('location_id', 'in', transit_internal_loc.ids),
                ('location_id', 'in', transit_internal_loc.ids),                
            ]
            moves = self.env['stock.move.line'].search(domain)
            total += sum(moves.mapped('quantity'))
        return total

    def get_delivery(self):
        total = 0
        for loc in self.location_id:
            src = loc
            dest = self.env['stock.location'].search([('usage', '=', 'customer')])
            moves = self.get_moves(src, dest)
            total += sum(moves.mapped('quantity'))
        return total
    
    def get_transfer_out(self):
        total = 0
        #move.location_id.id == helper.warehouse_id.lot_stock_id.id and move.location_dest_id.id in transit_loc.ids
        for loc in self.location_id:
            src = loc
            dest = self.env['stock.location'].search(['|',('usage', '=', 'transit'),('usage', '=', 'internal')])
            moves = self.get_moves(src, dest)
            total += sum(moves.mapped('quantity'))
        return total

    def get_adjustment_positive(self):
        total = 0
        for loc in self.location_id:
            src = self.product_id.with_company(self.env.company.id).property_stock_inventory
            dest = loc
            moves = self.get_moves(src, dest)
            total += sum(moves.mapped('quantity'))
        return total

    def get_adjustment_negative(self):
        total = 0
        for loc in self.location_id:
            src = loc
            dest = self.product_id.with_company(self.env.company.id).property_stock_inventory
            moves = self.get_moves(src, dest)
            total += sum(moves.mapped('quantity'))
        return total

    def get_warehouse_locations(self):
        # TODO: for now, just use stock location
        #return self.warehouse_id.lot_stock_id
        return self.location_id

    def get_qty(self, to_date):
        total = 0
        for loc in self.location_id:
            total += self.product_id.with_context({'location': loc.id, 'to_date': to_date}).qty_available
            # cache issue with context. without invalidating cache, previous location `qty_available` will be returned instead
            # https://github.com/odoo/odoo/issues/33641
            self.product_id.invalidate_model(['qty_available'])
        return total

    def get_stock_move(self):
        total = 0
        for loc in self.location_id:
            src = loc
            #dest = self.env['stock.location'].search(['|',('usage', '=', 'customer'),('usage', '=', 'supplier')])
            #_all_loc = dest.ids.append(src.id)
            domain = [
                ('product_id', '=', self.product_id.id), 
                ('date', '>', self.start_date), 
                ('date', '<', self.end_date), 
                ('state', '=', 'done'),
                '|',
                ('location_id', 'in', src.ids),
                ('location_dest_id', 'in', src.ids)
            ]
            moves = self.env['stock.move.line'].search(domain,order="date")
            total = moves
        return total
    
    def get_sale_return(self):
        total = 0
        for loc in self.location_id:
            src = loc
            dest = self.env['stock.location'].search([('usage', '=', 'customer')])
            moves = self.get_moves(dest, src)
            total += sum(moves.mapped('quantity'))
        return total

    def get_purchase_return(self):
        total = 0
        for loc in self.location_id:
            src = self.env['stock.location'].search([('usage', '=', 'supplier')])
            dest = loc
            moves = self.get_moves(dest, src)
            total += sum(moves.mapped('quantity'))
        return total

    def get_scrapped_in_total(self):
        total = 0
        scrapped_loc = self.env['stock.location'].search([('scrap_location', '=', True)])                    #Scrapped Location  
        for loc in self.location_id:
            src = loc
            dest = self.env['stock.location'].search([('usage', '=', 'customer')])
            moves = self.get_moves(src, scrapped_loc)
            total += sum(moves.mapped('quantity'))
        return total

    def get_scrapped_out_total(self):
        # try with different implemention (without loop)
        # not using loop and extract query at once will probably improve performance
        src = self.env['stock.location'].search([('scrap_location', '=', True)])
        dest = self.location_id
        moves = self.get_moves(src, dest)
        total = sum(moves.mapped('quantity'))
        return total

    def get_manufacture_in(self):
        total = 0
        for loc in self.location_id:
            dest = loc
            src = self.env['stock.location'].search([('usage', '=', 'production')])
            moves = self.get_moves(src, dest)
            total += sum(moves.mapped('quantity'))
        return total

    def get_manufacture_out(self):
        total = 0
        for loc in self.location_id:
            src = loc
            dest = self.env['stock.location'].search([('usage', '=', 'production')])
            moves = self.get_moves(src, dest)
            total += sum(moves.mapped('quantity'))
        return total