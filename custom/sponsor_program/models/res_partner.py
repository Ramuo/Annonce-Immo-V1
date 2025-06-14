from odoo import models, fields, api



class ResPartner(models.Model):
    _inherit = "res.partner"


    sponsor_ids = fields.One2many('sponsorship.relationship','sponsor_id', string="Parrain")
    sponsored_ids = fields.One2many('sponsorship.relationship','sponsor_id', string="Parrainé")

    sponsored_count = fields.Integer(string='Nbre parrainé', compute="_compute_sponsored_count")

    #Compute Nbre parrainé
    @api.depends('sponsored_ids')
    def _compute_sponsored_count(self):
        for rec in self:
            rec.sponsored_count = len(rec.sponsored_ids)

    # Action methods for contacts to view sponsored
    def action_open_sponsored_contacts(self):
        self.ensure_one()
        return{
            'type': 'ir.actions.act_window',
            'name': 'Parrainé',
            'res_model': 'sponsorship.relationship',
            'view_mode': 'list,form',
            'domain': [('sponsor_id', '=', self.id)],
            'context': {'default_sponsor_id': self.id}
        }

    # Action methods for contacts to view sponsor
    def action_open_sponsor_of(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Parrain',
            'res_model': 'sponsorship.relationship',
            'view_mode': 'list,form',
            'domain': [('sponsored_id', '=', self.id)],
            'context': {'default_sponsored_id': self.id}
        }