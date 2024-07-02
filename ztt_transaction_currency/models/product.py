
from odoo import _, api, fields, models
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit="product.template"

    #sale_renting
    def _get_best_pricing_rule(self, product=False, start_date=False, end_date=False, **kwargs):
        """ Return the best pricing rule for the given duration.

        :param ProductProduct product: a product recordset (containing at most one record)
        :param datetime start_date: start date of leasing period
        :param datetime end_date: end date of leasing period
        :return: least expensive pricing rule for given duration
        """
        self.ensure_one()
        best_pricing_rule = self.env['product.pricing']
        if not self.product_pricing_ids or not (start_date and end_date):
            return best_pricing_rule
        pricelist = kwargs.get('pricelist', self.env['product.pricelist'])
        currency = kwargs.get('currency', self.currency_id)
        company = kwargs.get('company', self.env.company)
        duration_dict = self.env['product.pricing']._compute_duration_vals(start_date, end_date)
        min_price = float("inf")  # positive infinity
        available_pricings = self.env['product.pricing']._get_suitable_pricings(
            product or self, pricelist=pricelist
        )
        for pricing in available_pricings:
            unit = pricing.recurrence_id.unit
            price = pricing._compute_price(duration_dict[unit], unit)
            if pricing.currency_id != currency:
                # price = pricing.currency_id._convert(
                #     from_amount=price,
                #     to_currency=currency,
                #     company=company,
                #     date=fields.Date.today(),
                # )
                price = pricing.currency_id._convert(
                    from_amount=price,
                    to_currency=currency,
                    company=company,
                    date=fields.Date.today(),
                )
            if price < min_price:
                min_price, best_pricing_rule = price, pricing
        return best_pricing_rule

    def _price_compute(self, price_type, uom=None, currency=None, company=None, date=False):
        company = company or self.env.company
        date = date or fields.Date.context_today(self)

        self = self.with_company(company)
        if price_type == 'standard_price':
            # standard_price field can only be seen by users in base.group_user
            # Thus, in order to compute the sale price from the cost for users not in this group
            # We fetch the standard price as the superuser
            self = self.sudo()

        prices = dict.fromkeys(self.ids, 0.0)
        for template in self:
            price = template[price_type] or 0.0
            price_currency = template.currency_id
            if price_type == 'standard_price':
                if not price and template.product_variant_ids:
                    price = template.product_variant_ids[0].standard_price
                price_currency = template.cost_currency_id
            elif price_type == 'list_price':
                price += template._get_attributes_extra_price()

            if uom:
                price = template.uom_id._compute_price(price, uom)

            # Convert from current user company currency to asked one
            # This is right cause a field cannot be in more than one currency
            if currency:
                # price = price_currency._convert(price, currency, company, date)
                price = price_currency._convert(price, currency, company, date)

            prices[template.id] = price
        return prices


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _price_compute(self, price_type, uom=None, currency=None, company=None, date=False):
        company = company or self.env.company
        date = date or fields.Date.context_today(self)
        self = self.with_company(company)
        if price_type == 'standard_price':
            # standard_price field can only be seen by users in base.group_user
            # Thus, in order to compute the sale price from the cost for users not in this group
            # We fetch the standard price as the superuser
            self = self.sudo()

        prices = dict.fromkeys(self.ids, 0.0)
        for product in self:
            price = product[price_type] or 0.0
            price_currency = product.currency_id
            if price_type == 'standard_price':
                price_currency = product.cost_currency_id
            elif price_type == 'list_price':
                price += product._get_attributes_extra_price()

            if uom:
                price = product.uom_id._compute_price(price, uom)

            # Convert from current user company currency to asked one
            # This is right cause a field cannot be in more than one currency
            if currency:
                # price = price_currency._convert(price, currency, company, date)
                price = price_currency._convert(price, currency, company, date)

            prices[product.id] = price

        return prices

    def _get_contextual_discount(self):
        self.ensure_one()
        pricelist = self.product_tmpl_id._get_contextual_pricelist()
        if not pricelist:
            # No pricelist = no discount
            return 0.0

        # lst_price = self.currency_id._convert(
        #     self.lst_price,
        #     pricelist.currency_id,
        #     self.env.company,
        #     fields.Datetime.now(),
        # )
        lst_price = self.currency_id._convert(
            self.lst_price,
            pricelist.currency_id,
            self.env.company,
            fields.Datetime.now(),
        )
        if lst_price:
            return (lst_price - self._get_contextual_price()) / lst_price
        return 0.0


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    #sale_renting
    def _compute_price_rule(
        self, products, quantity, currency=None, date=False, start_date=None, end_date=None,
        **kwargs
    ):
        """ Override to handle the rental product price

        Note that this implementation can be done deeper in the base price method of pricelist item
        or the product price compute method.
        """
        self and self.ensure_one()  # self is at most one record

        currency = currency or self.currency_id or self.env.company.currency_id
        currency.ensure_one()

        if not products:
            return {}

        if not date:
            # Used to fetch pricelist rules and currency rates
            date = fields.Datetime.now()

        results = {}
        if self._enable_rental_price(start_date, end_date):
            rental_products = products.filtered('rent_ok')
            Pricing = self.env['product.pricing']
            for product in rental_products:
                if start_date and end_date:
                    pricing = product._get_best_pricing_rule(
                        start_date=start_date, end_date=end_date, pricelist=self, currency=currency
                    )
                    duration_vals = Pricing._compute_duration_vals(start_date, end_date)
                    duration = pricing and duration_vals[pricing.recurrence_id.unit or 'day'] or 0
                else:
                    pricing = Pricing._get_first_suitable_pricing(product, self)
                    duration = pricing.recurrence_id.duration

                if pricing:
                    price = pricing._compute_price(duration, pricing.recurrence_id.unit)
                elif product._name == 'product.product':
                    price = product.lst_price
                else:
                    price = product.list_price
                # results[product.id] = pricing.currency_id._convert(
                #     price, currency, self.env.company, date
                # ), False
                results[product.id] = pricing.currency_id._convert(
                    price, currency, self.env.company, date
                ), False

        price_computed_products = self.env[products._name].browse(results.keys())
        return {
            **results,
            **super()._compute_price_rule(
                products - price_computed_products, quantity, currency=currency, date=date, **kwargs
            ),
        }


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _compute_base_price(self, product, quantity, uom, date, currency):
        """ Compute the base price for a given rule

        :param product: recordset of product (product.product/product.template)
        :param float qty: quantity of products requested (in given uom)
        :param uom: unit of measure (uom.uom record)
        :param datetime date: date to use for price computation and currency conversions
        :param currency: currency in which the returned price must be expressed

        :returns: base price, expressed in provided pricelist currency
        :rtype: float
        """
        currency.ensure_one()

        rule_base = self.base or 'list_price'
        if rule_base == 'pricelist' and self.base_pricelist_id:
            price = self.base_pricelist_id._get_product_price(
                product, quantity, currency=self.base_pricelist_id.currency_id, uom=uom, date=date
            )
            src_currency = self.base_pricelist_id.currency_id
        elif rule_base == "standard_price":
            src_currency = product.cost_currency_id
            price = product._price_compute(rule_base, uom=uom, date=date)[product.id]
        else: # list_price
            src_currency = product.currency_id
            price = product._price_compute(rule_base, uom=uom, date=date)[product.id]

        if src_currency != currency:
            price = src_currency._convert(price, currency, self.env.company, date, round=False)

        return price