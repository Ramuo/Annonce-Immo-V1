from odoo import models, fields, api



class TypeBien(models.Model):
    _name = 'type.bien'
    _description = 'type de bien immobilier'



    name = fields.Char(string='Nom', required=True)
    