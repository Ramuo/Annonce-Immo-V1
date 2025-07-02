from odoo import models, fields


class SponsorshipRewardType(models.Model):
    _name = 'sponsorship.reward.type'
    _description = 'Sponsor Reward Type'


    name = fields.Char(string='Nom', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean("Actif", default=True)