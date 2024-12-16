# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    backdate_for_picking = fields.Boolean("Enable Backdate for Picking")
    remark_for_picking = fields.Boolean("Enable Remark for Picking")
    remark_mandatory_for_picking = fields.Boolean(
        "Remark Mandatory for Picking")
    backdate_for_scrap = fields.Boolean("Enable Backdate for Scrap")
    remark_for_scrap = fields.Boolean("Enable Remark for Scrap")
    remark_mandatory_for_scrap = fields.Boolean("Remark Mandatory for Scrap")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    backdate_for_picking = fields.Boolean(
        "Enable Backdate for Picking", related="company_id.backdate_for_picking", readonly=False)
    remark_for_picking = fields.Boolean(
        "Enable Remark for Picking", related="company_id.remark_for_picking", readonly=False)
    remark_mandatory_for_picking = fields.Boolean(
        "Remark Mandatory for Picking", related="company_id.remark_mandatory_for_picking", readonly=False)
    backdate_for_scrap = fields.Boolean(
        "Enable Backdate for Scrap", related="company_id.backdate_for_scrap", readonly=False)
    remark_for_scrap = fields.Boolean(
        "Enable Remark for Scrap", related="company_id.remark_for_scrap", readonly=False)
    remark_mandatory_for_scrap = fields.Boolean(
        "Remark Mandatory for Scrap", related="company_id.remark_mandatory_for_scrap", readonly=False)
