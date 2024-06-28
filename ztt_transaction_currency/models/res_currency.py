# -*- coding: utf-8 -*-

from typing import Dict, List
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang
from odoo.tools.float_utils import float_compare, float_round
import logging
_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def _convert(self, from_amount, to_currency, company=None, date=None, round=True):  # noqa: A002 builtin-argument-shadowing
        """Returns the converted amount of ``from_amount``` from the currency
           ``self`` to the currency ``to_currency`` for the given ``date`` and
           company.

           :param company: The company from which we retrieve the convertion rate
           :param date: The nearest date from which we retriev the conversion rate.
           :param round: Round the result or not
        """
        to_currency_rate = to_currency._context.get('currency_rate',0)
        from_currency_rate = self._context.get('currency_rate',0)
        currency_rate = to_currency_rate/from_currency_rate if from_currency_rate else to_currency_rate
        _logger.debug('FROM %s, TO %s, Rate %s'%(to_currency_rate,from_currency_rate,currency_rate))
        self, to_currency = self or to_currency, to_currency or self
        assert self, "convert amount from unknown currency"
        assert to_currency, "convert amount to unknown currency"
        # apply conversion rate
        if from_amount:
            _logger.debug('################### FROM Currency %s, To Currency %s, RATE %s, FROM Amount %s'%(self.name,to_currency.name,currency_rate,from_amount))
            if currency_rate==0:
                currency_rate = self._get_conversion_rate(self, to_currency, company, date)
            elif self.id==to_currency.id:
                currency_rate = 1
            else:
                currency_rate = 1/currency_rate
            to_amount = from_amount * currency_rate
            _logger.debug('################### FROM Currency %s, To Currency %s, RATE %s, FROM Amount %s, TO Amount %s'%(self.name,to_currency.name,currency_rate,from_amount,to_amount))
        else:
            return 0.0

        # apply rounding
        return to_currency.round(to_amount) if round else to_amount

    