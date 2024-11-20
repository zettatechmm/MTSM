# -*- coding: utf-8 -*-
#############################################################################
#############################################################################
from odoo import fields, models


class ProductPricelist(models.Model):
    """Inherits the Product Pricelist to update the _compute_price_rule
     function for adding the product uom in price rule."""
    _inherit = "product.pricelist"

    def _compute_price_rule(
            self, products, quantity, currency=None, uom=None, date=False,
            compute_price=True,
            **kwargs
    ):
        """ Low-level method - Mono pricelist, multi products
        Returns: dict{product_id: (price, suitable_rule) for the given
        price list}
        :param products: recordset of products
        (product.product/product.template)
        :param float qty: quantity of products requested (in given uom)
        :param uom: unit of measure (uom.uom record)
            If not specified, prices returned are expressed in product uoms
        :param date: date to use for price computation and currency conversions
        :type date: date or datetime
        :returns: product_id: (price, pricelist_rule)
        :rtype: dict
        """
        self.ensure_one()
        if not products:
            return {}
        if not date:
            date = fields.Datetime.now()
        rules = self._get_applicable_rules(products, date, **kwargs)
        results = {}
        for product in products:
            suitable_rule = self.env['product.pricelist.item']
            target_uom = uom or product.uom_id
            for rule in rules:
                if rule._is_applicable_for(product, quantity, uom):
                    suitable_rule = rule
                    break
            kwargs['pricelist'] = self
            price = suitable_rule._compute_price(product, quantity, target_uom,
                                                 date=date,
                                                 currency=self.currency_id)
            results[product.id] = (price, suitable_rule.id)
            if compute_price:
                price = suitable_rule._compute_price(
                    product, quantity, target_uom, date=date,
                    currency=currency)
            else:
                # Skip price computation when only the rule is requested.
                price = 0.0
            results[product.id] = (price, suitable_rule.id)
        return results
