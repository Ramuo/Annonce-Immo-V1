from odoo import fields, models, api




class OffreBien(models.Model):
    _name = 'offre.bien'
    _description = 'Offres des biens'





    price = fields.Float(string='Prix')
    status = fields.Selection([
        ('accepted', 'Accepté'),
        ('refused', 'Refusé'),
    ], string='Statut')
    partner_id = fields.Many2one('res.partner', string='Client')
    property_id = fields.Many2one('bien.immobilier', string='Bien')

    validity = fields.Integer(string='Validité')
    deadline = fields.Date(string='Date Limite')

