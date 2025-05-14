from odoo import fields, models, api




class ParticulariteBien(models.Model):
    _name='particularite.bien'
    _description='Particularité du Bien'



    name = fields.Char(string='Nom', required=True)
    color = fields.Integer(string="Color")



