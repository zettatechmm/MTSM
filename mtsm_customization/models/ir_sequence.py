import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class IrSequence(models.Model):
    _inherit = 'ir.sequence'
    
    branch_id = fields.Many2one("x_branches", string="Branch")
    
    @api.model
    def next_by_code_by_branch(self, sequence_code, sequence_date=None, branch_id=None):
        """ Draw an interpolated string using a sequence with the requested code.
            If several sequences with the correct code are available to the user
            (multi-company cases), the one from the user's current company will
            be used.
        """
        self.check_access_rights('read')
        company_id = self.env.company.id
        seq_ids = self.search([('code', '=', sequence_code), ('company_id', 'in', [company_id, False]), ('branch_id', '=', branch_id)], order='company_id')
        if not seq_ids:
            _logger.debug("No ir.sequence has been found for code '%s'. Please make sure a sequence is set for current company." % sequence_code)
            return False
        seq_id = seq_ids[0]
        return seq_id._next(sequence_date=sequence_date)
    
    @api.onchange('branch_id')
    def _onchange_branch(self):
        if self.branch_id:
            self.prefix = self.branch_id.x_studio_code