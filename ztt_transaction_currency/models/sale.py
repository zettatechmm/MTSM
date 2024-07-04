# -*- coding: utf-8 -*-

from typing import Dict, List
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang
from odoo.tools.float_utils import float_compare, float_round
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    x_studio_branch = fields.Many2one("x_branches", default=lambda self: self.env.user.x_studio_default_branch.id)
    warehouse_id = fields.Many2one(
                    'stock.warehouse', string='Warehouse', required=True,
                    compute='_compute_warehouse_id', store=True, readonly=False, precompute=True,
                    check_company=True, domain="['|', ('x_studio_branch', '=', False), ('x_studio_branch', '=', x_studio_branch)]")
    
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
        res.update({'currency_rate': self.currency_rate,
                    'x_studio_branch': self.x_studio_branch.id,
                    'journal_id': self._get_default_journal().id,
                    'x_studio_ordered_by': self.x_studio_ordered_by_1.id,
                    'x_studio_salespersons': self.x_studio_salespersons.ids})    
        return res

    @api.depends('currency_id','pricelist_id')
    def compute_currency_rate(self):
        for rec in self:
            if rec.company_id.currency_id.id!=rec.currency_id.id:
                rec.currency_rate = rec.currency_id.rate
            else:
                rec.currency_rate = 1

    currency_rate = fields.Float('Currency Rate',default=1,compute='compute_currency_rate',store=True,readonly=False)

    @api.depends('invoice_ids.state', 'currency_id', 'amount_total','currency_rate')
    def _compute_amount_to_invoice(self):
        for order in self:
            # If the invoice status is 'Fully Invoiced' force the amount to invoice to equal zero and return early.
            if order.invoice_status == 'invoiced':
                order.amount_to_invoice = 0.0
                return

            order.amount_to_invoice = order.amount_total
            for invoice in order.invoice_ids.filtered(lambda x: x.state == 'posted'):
                prices = sum(invoice.line_ids.filtered(lambda x: order in x.sale_line_ids.order_id).mapped('price_total'))
                # invoice_amount_currency = invoice.currency_id._convert(
                #     prices * -invoice.direction_sign,
                #     order.currency_id,
                #     invoice.company_id,
                #     invoice.date,
                # )
                invoice_amount_currency = invoice.currency_id.with_context(currency_rate=invoice.currency_rate)._convert(
                    prices * -invoice.direction_sign,
                    order.currency_id.with_context(currency_rate=order.currency_rate),
                    invoice.company_id,
                    invoice.date,
                                    )
                order.amount_to_invoice -= invoice_amount_currency


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('invoice_lines', 'invoice_lines.price_total', 'invoice_lines.move_id.state', 'invoice_lines.move_id.move_type')
    def _compute_untaxed_amount_invoiced(self):
        """ Compute the untaxed amount already invoiced from the sale order line, taking the refund attached
            the so line into account. This amount is computed as
                SUM(inv_line.price_subtotal) - SUM(ref_line.price_subtotal)
            where
                `inv_line` is a customer invoice line linked to the SO line
                `ref_line` is a customer credit note (refund) line linked to the SO line
        """
        for line in self:
            amount_invoiced = 0.0
            for invoice_line in line._get_invoice_lines():
                if invoice_line.move_id.state == 'posted':
                    invoice_date = invoice_line.move_id.invoice_date or fields.Date.today()
                    if invoice_line.move_id.move_type == 'out_invoice':
                        # amount_invoiced += invoice_line.currency_id._convert(invoice_line.price_subtotal, line.currency_id, line.company_id, invoice_date)
                        amount_invoiced += invoice_line.currency_id.with_context(currency_rate=invoice_line.move_id.currency_rate)._convert(invoice_line.price_subtotal, line.currency_id.with_context(currency_rate=line.order_id.currency_rate), line.company_id, invoice_date)
                    elif invoice_line.move_id.move_type == 'out_refund':
                        # amount_invoiced -= invoice_line.currency_id._convert(invoice_line.price_subtotal, line.currency_id, line.company_id, invoice_date)
                        amount_invoiced -= invoice_line.currency_id.with_context(currency_rate=invoice_line.move_id.currency_rate)._convert(invoice_line.price_subtotal, line.currency_id.with_context(currency_rate=line.order_id.currency_rate), line.company_id, invoice_date)
            line.untaxed_amount_invoiced = amount_invoiced

    @api.depends('state', 'product_id', 'untaxed_amount_invoiced', 'qty_delivered', 'product_uom_qty', 'price_unit')
    def _compute_untaxed_amount_to_invoice(self):
        """ Total of remaining amount to invoice on the sale order line (taxes excl.) as
                total_sol - amount already invoiced
            where Total_sol depends on the invoice policy of the product.

            Note: Draft invoice are ignored on purpose, the 'to invoice' amount should
            come only from the SO lines.
        """
        for line in self:
            amount_to_invoice = 0.0
            if line.state == 'sale':
                # Note: do not use price_subtotal field as it returns zero when the ordered quantity is
                # zero. It causes problem for expense line (e.i.: ordered qty = 0, deli qty = 4,
                # price_unit = 20 ; subtotal is zero), but when you can invoice the line, you see an
                # amount and not zero. Since we compute untaxed amount, we can use directly the price
                # reduce (to include discount) without using `compute_all()` method on taxes.
                price_subtotal = 0.0
                uom_qty_to_consider = line.qty_delivered if line.product_id.invoice_policy == 'delivery' else line.product_uom_qty
                price_reduce = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                price_subtotal = price_reduce * uom_qty_to_consider
                if len(line.tax_id.filtered(lambda tax: tax.price_include)) > 0:
                    # As included taxes are not excluded from the computed subtotal, `compute_all()` method
                    # has to be called to retrieve the subtotal without them.
                    # `price_reduce_taxexcl` cannot be used as it is computed from `price_subtotal` field. (see upper Note)
                    price_subtotal = line.tax_id.compute_all(
                        price_reduce,
                        currency=line.currency_id,
                        quantity=uom_qty_to_consider,
                        product=line.product_id,
                        partner=line.order_id.partner_shipping_id)['total_excluded']
                inv_lines = line._get_invoice_lines()
                if any(inv_lines.mapped(lambda l: l.discount != line.discount)):
                    # In case of re-invoicing with different discount we try to calculate manually the
                    # remaining amount to invoice
                    amount = 0
                    for l in inv_lines:
                        if len(l.tax_ids.filtered(lambda tax: tax.price_include)) > 0:
                            # amount += l.tax_ids.compute_all(l.currency_id._convert(l.price_unit, line.currency_id, line.company_id, l.date or fields.Date.today(), round=False) * l.quantity)['total_excluded']
                            amount += l.tax_ids.compute_all(l.currency_id.with_context(currency_rate=l.move_id.currency_rate)._convert(l.price_unit, line.currency_id.with_context(currency_rate=line.order_id.currency_rate), line.company_id, l.date or fields.Date.today(), round=False) * l.quantity)['total_excluded']
                        else:
                            # amount += l.currency_id._convert(l.price_unit, line.currency_id, line.company_id, l.date or fields.Date.today(), round=False) * l.quantity
                            amount += l.currency_id.with_context(currency_rate=l.move_id.currency_rate)._convert(l.price_unit, line.currency_id.with_context(currency_rate=line.order_id.currency_rate), line.company_id, l.date or fields.Date.today(), round=False) * l.quantity

                    amount_to_invoice = max(price_subtotal - amount, 0)
                else:
                    amount_to_invoice = price_subtotal - line.untaxed_amount_invoiced

            line.untaxed_amount_to_invoice = amount_to_invoice

    def _convert_to_sol_currency(self, amount, currency):
        """Convert the given amount from the given currency to the SO(L) currency.

        :param float amount: the amount to convert
        :param currency: currency in which the given amount is expressed
        :type currency: `res.currency` record
        :returns: converted amount
        :rtype: float
        """
        self.ensure_one()
        to_currency = self.currency_id or self.order_id.currency_id
        if currency and to_currency and currency != to_currency:
            conversion_date = self.order_id.date_order or fields.Date.context_today(self)
            company = self.company_id or self.order_id.company_id or self.env.company
            # return currency._convert(
            #     from_amount=amount,
            #     to_currency=to_currency,
            #     company=company,
            #     date=conversion_date,
            #     round=False,
            # )
            return currency._convert(
                from_amount=amount,
                to_currency=to_currency.with_context(currency_rate=self.order_id.currency_rate),
                company=company,
                date=conversion_date,
                round=False
            )
        return amount

    #sale_purchase module
    def _purchase_service_get_price_unit_and_taxes(self, supplierinfo, purchase_order):
        supplier_taxes = self.product_id.supplier_taxes_id.filtered(lambda t: t.company_id == purchase_order.company_id)
        taxes = purchase_order.fiscal_position_id.map_tax(supplier_taxes)
        if supplierinfo:
            price_unit = self.env['account.tax'].sudo()._fix_tax_included_price_company(supplierinfo.price, supplier_taxes, taxes, purchase_order.company_id)
            if purchase_order.currency_id and supplierinfo.currency_id != purchase_order.currency_id:
                # price_unit = supplierinfo.currency_id._convert(
                #     price_unit,
                #     purchase_order.currency_id,
                #     purchase_order.company_id,
                #     fields.Date.context_today(self)
                # )
                price_unit = supplierinfo.currency_id.with_context(currency_rate=supplierinfo.currency_id.rate)._convert(
                    price_unit,
                    purchase_order.currency_id.with_context(currency_rate=purchase_order.currency_rate),
                    purchase_order.company_id,
                    fields.Date.context_today(self),
                )
        else:
            price_unit = 0.0
        return price_unit, taxes