# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast
import datetime
import io
import json
import logging
import math
import re
import base64
from ast import literal_eval
from collections import defaultdict
from functools import cmp_to_key

import markupsafe
from babel.dates import get_quarter_names
from dateutil.relativedelta import relativedelta

from odoo.addons.web.controllers.utils import clean_action
from odoo import models, api, _

class AccountReport(models.Model):
    _inherit = 'account.report'
    
    ####################################################
    # OPTIONS: partners
    ####################################################

    def _init_options_partner(self, options, previous_options=None):
        super()._init_options_partner(options, previous_options)
        # #Partner Branch
        options['partner_branches'] = previous_options and previous_options.get('partner_branches') or []
        selected_partner_branch_ids = [int(category) for category in options['partner_branches']]
        selected_partner_branches = selected_partner_branch_ids and self.env['x_branches'].browse(selected_partner_branch_ids) or self.env['x_branches']
        options['selected_partner_branches'] = selected_partner_branches.mapped('x_name')
       
        #Partner Township
        options['partner_townships'] = previous_options and previous_options.get('partner_townships') or []
        selected_partner_township_ids = [int(category) for category in options['partner_townships']]
        selected_partner_townships = selected_partner_township_ids and self.env['res.township'].browse(selected_partner_township_ids) or self.env['res.township']
        options['selected_partner_townships'] = selected_partner_townships.mapped('name')
        
        #Partner State
        options['partner_states'] = previous_options and previous_options.get('partner_states') or []
        selected_partner_state_ids = [int(category) for category in options['partner_states']]
        selected_partner_states = selected_partner_state_ids and self.env['res.country.state'].browse(selected_partner_state_ids) or self.env['res.country.state']
        options['selected_partner_states'] = selected_partner_states.mapped('name')
        
    @api.model
    def _get_options_partner_domain(self, options):
        domain =  super()._get_options_partner_domain(options)
        if options.get('partner_townships'):
            partner_township_ids = [int(township) for township in options['partner_townships']]
            domain.append(('partner_id.township_id', 'in', partner_township_ids))
            
        if options.get('partner_states'):
            partner_state_ids = [int(township) for township in options['partner_states']]
            domain.append(('partner_id.state_id', 'in', partner_state_ids))
            
        if options.get('partner_branches'):
            partner_branch_ids = [int(branch) for branch in options['partner_branches']]
            domain.append(('partner_id.x_studio_branch', 'in', partner_branch_ids))
        return domain


    ####################################################
    # OPTIONS: account code
    ####################################################

    def _init_options_account_code(self, options, previous_options=None):
        domain = [] 
        options['account_codes'] = previous_options and previous_options.get('account_codes') or []        
        selected_account_code_ids = [int(account) for account in options['account_codes']]       
        selected_account_codes = selected_account_code_ids and self.env['account.account'].browse(selected_account_code_ids) or self.env['account.account'].search(domain)     
        options['selected_account_codes'] = selected_account_codes.mapped('name')  

        options['account_tags'] = previous_options and previous_options.get('account_tags') or []        
        selected_account_tag_ids = [int(account) for account in options['account_tags']]       
        selected_account_tags = selected_account_tag_ids and self.env['account.account.tag'].browse(selected_account_tag_ids) or self.env['account.account.tag'].search(domain)     
        options['selected_account_tags'] = selected_account_tags.mapped('name') 

    @api.model
    def _get_options_account_code_domain(self, options):
        domain = []
        domain.append(('company_id', '=', self.env.user.company_id.id))
        if options.get('account_codes'):
            selected_account_code_ids = [int(code) for code in options['account_codes']]
            domain.append(('account_id', 'in', selected_account_code_ids))

        if options.get('account_tags'):
            selected_account_tag_ids = [int(code) for code in options['account_tags']]
            domain.append(('account_id.tag_ids', 'in', selected_account_tag_ids))
        return domain
    
    def _get_options_domain(self, options, date_scope):
        self.ensure_one()
        domain = super()._get_options_domain(options, date_scope)
        domain += self._get_options_account_code_domain(options)

        return domain