# -*- coding: utf-8 -*-
#############################################################################
#############################################################################
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_pricelist_price(self):
        """Compute the price given by the pricelist for the given line information.

        :return: the product sales price in the order currency (without taxes)
        :rtype: float
        """
        self.ensure_one()
        self.product_id.ensure_one()
        uom  = self.product_uom
        if self.pricelist_item_id:
            if self.pricelist_item_id.applied_on == '0_product_variant':
                uom = self.pricelist_item_id.product_id.uom_id
            elif self.pricelist_item_id.applied_on == '1_product':
                uom = self.pricelist_item_id.product_tmpl_id.uom_id
            else:
                uom = self.product_uom
        price = self.pricelist_item_id._compute_price(
            product=self.product_id.with_context(**self._get_product_price_context()),
            quantity=self.product_uom_qty or 1.0,
            uom=uom,
            date=self.order_id.date_order,
            currency=self.currency_id,
        )

        return price