from odoo import models, fields, api


class SponsorshipType(models.Model):
    _name = 'sponsorship.type'
    _description ='Sponsorship type'


    name = fields.Char(string='Nom', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    