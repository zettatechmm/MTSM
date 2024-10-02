from odoo import api, fields, models
from . import odoo_datetime_helper
from datetime import datetime, timedelta
import xlwt
from io import BytesIO
import base64


class TransitionReportWizard(models.TransientModel):
    _name = 'transition.report.wizard'
    _description = "Transaction Report Wizard"

    def warehouse_id_domain(self):
        if self.env.user.location_ids:
            return [('id', 'in', self.env.user.location_ids.ids)]
        else:
            return [(1, '=', 1)]
        
    def _get_start_date(self):
        dt = datetime.now()
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        dt = dt - timedelta(hours=6, minutes=30)
        return dt

    def _get_end_date(self):
        dt = datetime.now()
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=59)
        dt = dt - timedelta(hours=6, minutes=30)
        return dt

    start_date = fields.Datetime(string='Start Date', default=_get_start_date)
    end_date = fields.Datetime(string='End Date', default=_get_end_date)
    location_ids = fields.Many2many('stock.location', string='Location')
    product_ids = fields.Many2many('product.product', domain=[('type', '=', 'product')], string='Product')
    excel_file = fields.Binary()
    is_all_products = fields.Boolean(string="All Products")
    is_all_locations = fields.Boolean(string="All Locations")

    @api.onchange('is_all_products')
    def _onchange_is_all_products(self):
        for rec in self:
            rec.product_ids = False

    @api.onchange('is_all_locations')
    def _onchange_is_all_locations(self):
        for rec in self:
            rec.location_ids = False

    def _get_data(self):
        data = []
        company_currency = self.env.user.company_id.currency_id
        rp_product_ids = self.product_ids if not self.is_all_products \
            else self.env['product.product'].sudo().search([('detailed_type', '=', 'product')])
        rp_location_ids = self.location_ids if not self.is_all_locations \
            else self.env['stock.location'].sudo().search(['&', '|',
                ('company_id', '=', False), 
                ('company_id', '=', self.env.company.id), 
                ('usage', 'in', ('internal','transit'))])
        for wh in rp_location_ids:
            for product in rp_product_ids:
                helper = self.env['stock.report.helper'].create({
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'location_id': wh.id,
                        'product_id': product.id,
                })

                opening_qty = helper.get_qty(self.start_date)
                opening_row = {
                    'default_code': product.default_code,
                    'description' : product.name,
                    'uom' : product.uom_id.name,
                    'date':odoo_datetime_helper.local_time(helper.start_date,'Asia/Yangon'),
                    'wh_name': wh.display_name,
                    'lot_no':'',
                    'expired_date': '',
                    'reference':'Opening',
                    'from':'',
                    'to':'',
                    'opening' : opening_qty,
                    'delivery' : '',
                    'sale_return':'',
                    'receiving' : '',  
                    'purchase_return':'',                  
                    'transfer_in' : '',
                    'transfer_out' : '',
                    'adjustment_positive': '',
                    'adjustment_negative': '',
                    'scrapped_in': '',
                    'scrapped_out': '',
                    # 'manufacture_in': '',
                    # 'manufacture_out': '',
                    'closing': '',
                    # 'cost': '',
                    # 'price' :'',
                    # 'currency': company_currency.name,
                }
                if helper.get_stock_move():  
                    data.append(opening_row)              
                customer_loc = self.env['stock.location'].search([('usage', '=', 'customer')])                                              #Customer Location
                supplier_loc = self.env['stock.location'].search([('usage', '=', 'supplier')])                                              #Supplier Location
                adjustment_loc = product.with_company(self.env.company.id).property_stock_inventory                                 #Adjustment Location
                scrapped_loc = self.env['stock.location'].search([('scrap_location', '=', True)])                                           #Scrapped Location   
                #transit_loc = self.env['stock.location'].search([('usage', '=', 'transit')])                                                #Transit Location
                #internal_loc = self.env['stock.location'].search([('usage', '=', 'internal')])                                              #Internal Location
                transit_internal_loc = self.env['stock.location'].search(['|',('usage', '=', 'transit'),('usage', '=', 'internal')])        #Transit Locations and Internal Locations
                production_loc = self.env['stock.location'].search([('usage', '=', 'production')])                                            #Production Location
                for move in helper.get_stock_move():
                    stock_valuation_cost = self._compute_valuation_cost(move.move_id)
                    #delivery
                    if move.location_id.id == helper.location_id.id and move.location_dest_id.id in customer_loc.ids:
                        delivery = self._compute_ref_uom_qty(move)
                    else:
                        delivery = 0
                    
                    #sale return
                    if move.location_id.id in customer_loc.ids and move.location_dest_id.id == helper.location_id.id:
                        sale_return = self._compute_ref_uom_qty(move)
                    else:
                        sale_return = 0
                    
                    #receiving
                    if move.location_id.id in supplier_loc.ids and move.location_dest_id.id == helper.location_id.id:
                        receiving = self._compute_ref_uom_qty(move)
                    else:
                        receiving = 0
                    
                    #purchase return
                    if move.location_id.id == helper.location_id.id and move.location_dest_id.id in supplier_loc.ids:
                        purchase_return = self._compute_ref_uom_qty(move)
                    else:
                        purchase_return = 0
                                            
                    #transfer_in
                    if move.location_id.id in transit_internal_loc.ids and move.location_dest_id.id == helper.location_id.id:
                        transfer_in = self._compute_ref_uom_qty(move)
                    else:
                        transfer_in = 0

                    #transfer_out
                    if move.location_id.id == helper.location_id.id and move.location_dest_id.id in transit_internal_loc.ids:
                        transfer_out = self._compute_ref_uom_qty(move)
                    else:
                        transfer_out = 0

                    #adjustment_positive
                    if move.location_id.id in adjustment_loc.ids and move.location_dest_id.id == helper.location_id.id:
                        adjustment_positive = self._compute_ref_uom_qty(move)
                    else:
                        adjustment_positive = 0     

                    #adjustment_negative
                    if move.location_id.id == helper.location_id.id and move.location_dest_id.id in adjustment_loc.ids:
                        adjustment_negative = self._compute_ref_uom_qty(move)
                    else:
                        adjustment_negative = 0 

                    #Scrapped (In)
                    if move.location_id.id == helper.location_id.id and move.location_dest_id.id in scrapped_loc.ids:
                        scrapped = self._compute_ref_uom_qty(move)
                    else:
                        scrapped = 0

                    # Scrapped (Out)
                    if move.location_id.id in scrapped_loc.ids and move.location_dest_id.id == helper.location_id.id:
                        scrapped_out = self._compute_ref_uom_qty(move)
                    else:
                        scrapped_out = 0

                    # # Manufacture (In)
                    # if move.location_id.id in production_loc.ids and move.location_dest_id.id == helper.location_id.id:
                    #     manufacture_in = self._compute_ref_uom_qty(move)
                    # else:
                    #     manufacture_in = 0

                    # # Manufacture (Out)
                    # if move.location_id.id == helper.location_id.id and move.location_dest_id.id in production_loc.ids:
                    #     manufacture_out = self._compute_ref_uom_qty(move)
                    # else:
                    #     manufacture_out = 0
                    
                    closing_qty = (opening_qty + sale_return + receiving + transfer_in + adjustment_positive + scrapped_out) -\
                        (delivery + purchase_return + transfer_out + adjustment_negative + scrapped)
                    
                    _row = {
                        'default_code': product.default_code,
                        'description' : product.name,
                        'uom' : product.uom_id.name,
                        'date': odoo_datetime_helper.local_time(move.date,'Asia/Yangon'),
                        'wh_name': '',
                        'lot_no': move.lot_id.name,
                        'expired_date': odoo_datetime_helper.local_time(move.lot_id.expiration_date,'Asia/Yangon'),
                        'reference':move.reference,
                        'from': move.location_id.display_name,
                        'to': move.location_dest_id.display_name,                        
                        'opening' : opening_qty,
                        'delivery' : delivery if delivery != 0 else '',
                        'sale_return':sale_return if sale_return != 0 else '',
                        'receiving' : receiving if receiving != 0 else '',
                        'purchase_return':purchase_return if purchase_return != 0 else '',
                        'transfer_in' : transfer_in if transfer_in != 0 else '',
                        'transfer_out' : transfer_out if transfer_out != 0 else '',
                        'adjustment_positive': adjustment_positive if adjustment_positive != 0 else '',
                        'adjustment_negative': adjustment_negative if adjustment_negative != 0 else '',
                        'scrapped_in':scrapped if scrapped != 0 else '',
                        'scrapped_out': scrapped_out if scrapped_out != 0 else '',
                        # 'manufacture_in': manufacture_in if manufacture_in != 0 else '',
                        # 'manufacture_out': manufacture_out if manufacture_out != 0 else '',
                        'closing':closing_qty,
                        # 'cost': stock_valuation_cost,
                        # 'price': move.sale_line_id.price_unit,
                        # 'currency': company_currency.name,
                    }
                    data.append(_row)
                    opening_qty = closing_qty
                #Closing Row
                closing_row = {
                    'default_code': product.default_code,
                    'description' : product.name,
                    'uom' : product.uom_id.name,
                    'date': odoo_datetime_helper.local_time(helper.end_date,'Asia/Yangon'),
                    'wh_name': wh.display_name,
                    'lot_no': '',
                    'expired_date': '',
                    'reference':'Closing',
                    'from':'',
                    'to':'',                     
                    'opening' : '',
                    'delivery' : helper.get_delivery(),
                    'sale_return': helper.get_sale_return(),
                    'receiving' : helper.get_receiving(),
                    'purchase_return': helper.get_purchase_return(),                   
                    'transfer_in' : helper.get_transfer_in(),
                    'transfer_out' : helper.get_transfer_out(),
                    'adjustment_positive': helper.get_adjustment_positive(),
                    'adjustment_negative': helper.get_adjustment_negative(),
                    'scrapped_in': helper.get_scrapped_in_total(),
                    'scrapped_out': helper.get_scrapped_out_total(),
                    # 'manufacture_in': helper.get_manufacture_in(),
                    # 'manufacture_out': helper.get_manufacture_out(),
                    'closing': helper.get_qty(self.end_date),
                    # 'cost':'',
                    # 'price':'',  
                    # 'currency':company_currency.name,
                }
                if helper.get_stock_move():  
                    data.append(closing_row)                                

        return data

    def _data(self):
        return {
            'start_date': odoo_datetime_helper.local_time(self.start_date, 'Asia/Yangon'),
            'end_date': odoo_datetime_helper.local_time(self.end_date, 'Asia/Yangon'),
            'data': self._get_data(),
        }

    def print_report_xls(self):
        # styles
        title_style = xlwt.easyxf('font: bold on, height 280; align: horiz center;')
        foot_style = xlwt.easyxf('font: bold on;')

        # prepare excel
        da = self._data()
        wb = xlwt.Workbook()
        sht = wb.add_sheet('Transition Report')
        # freeze header
        sht.set_panes_frozen(True)
        sht.set_horz_split_pos(2)

        sht.write_merge(0, 0, 0, 14, 'Stock Ledger Report(Detail) \n For the Period Between ' \
        + da['start_date'] + ' and ' + da['end_date'] , title_style)
        sht.row(0).height = 256*3

        header = ['No.', 'Product Code', 'Product Name', 'UoM', 'Date', 'Location Name', 'Lot No', 'Expired Date', 'Reference', 'From', 'To', 'Opening',
        'Sale Quantity', 'Sale Return', 'Purchase Quantity', 'Purchase Return', 'Transfer/in', 'Transfer/Out', 'Adjust (+)',  'Adjust (-)', 'Scrapped In', 'Scrapped Out', 'Closing']
        # main data
        body_data = da['data']
        if len(body_data) > 0:
            # NOTE: it seem dict keys are returned in order. but not sure
            # use fix dictionary for temp solution on python 3.5 server
            # ! since odoo 13 use at least python3.6, explicit body_keys is no longer needed
            body_keys = ['default_code', 'description', 'uom', 'date', 'wh_name', 'lot_no', 'expired_date', 'reference', 'from', 'to', 'opening',
                        'delivery', 'sale_return','receiving', 'purchase_return', 'transfer_in', 'transfer_out',
                        'adjustment_positive', 'adjustment_negative', 'scrapped_in', 'scrapped_out', 'closing']
        # +2 for title and header, start from 1 to skip title
        # for row in range(1, len(self.product_ids) + 2):
        for row in range(1, len(body_data) + 2):
            for col in range(len(header)):
                # header
                if row == 1:
                    sht.write(row, col, header[col])
                else:
                    # No. column
                    if col == 0:
                        body_data_row = row - 2
                        if body_data[body_data_row]['reference'] == "Closing":
                            sht.write(row, col, row - 1,foot_style)
                        else:
                            sht.write(row, col, row - 1)
                    # other columns
                    else:
                        body_data_row = row - 2
                        key = body_keys[col - 1]
                        if body_data[body_data_row]['reference'] == "Closing":
                            sht.write(row, col, body_data[body_data_row][key],foot_style)
                        else:
                            sht.write(row, col, body_data[body_data_row][key])

        # footnote
        # sht.write_merge(len(self.product_ids) + 3, len(self.product_ids) + 3, 0, 14, \
        # 'Note: Data in Opening, Receiving, Transfer and Closing only consider good products (exclude damage products)', foot_style)

        # download excel
        stream = BytesIO()
        wb.save(stream)
        self.excel_file = base64.encodebytes(stream.getvalue())
        filename = 'Stock Ledger Report(Detail) - ' + ' - ' + da['start_date'] + ' to ' + da['end_date']
        
        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': '/web/content/transition.report.wizard/%s/excel_file/%s.xls?download=true' %(self.id, filename),
        }

    def _compute_valuation_cost(self, move):
        stock_price_unit = 0
        if move.stock_valuation_layer_ids:
            for stock_valuation_record in move.stock_valuation_layer_ids:
                stock_price_unit = stock_valuation_record.unit_cost
        return stock_price_unit


    def _compute_ref_uom_qty(self, move):
        return move.quantity
        # config = self.env["ir.config_parameter"].sudo().get_param("stock_ledger_detail_report.uom")
        # if config:
        #     if config == 'origin':
        #         return move.quantity
        # if move.product_uom.uom_type == 'reference':
        #     return move.quantity
        # else:
        #     ref_uom = self.env['uom.uom'].search([
        #         ('category_id', '=', move.product_uom.category_id.id),
        #         ('uom_type', '=', 'reference'),
        #     ])
        #     return move.product_uom._compute_quantity(move.quantity, ref_uom)
