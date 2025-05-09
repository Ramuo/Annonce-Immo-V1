from odoo import models, fields

class Bien(models.Model):
    _name = "bien.immobilier"
    _description = "Annonce de Biens Immobiliers"

    name = fields.Char(string="Nom", required=True)
    type_id = fields.Many2one('type.bien', string='Type de bien')
    description = fields.Text(string="Description")
    postcode = fields.Char(string="Code Postal")
    date_availability = fields.Date(string="Disponible Le")
    expected_price = fields.Float(string="Prix Attendu")
    best_offer = fields.Float(string="Meilleure Offre")
    selling_price = fields.Float(string="Prix de Vente")
    bedrooms = fields.Integer(string="Chambres")
    living_area = fields.Integer(string="Surface (m²)")
    facades = fields.Integer(string="Façades")
    garage = fields.Boolean(string="Garage", default=False)
    garden = fields.Boolean(string="Jardin", default=False)
    garden_area = fields.Integer(string="Surface Jardin")
    garden_orientation = fields.Selection(
        [
            ('north', 'Nord'), 
            ('south', 'Sud'), 
            ('east', 'Est'), 
            ('west', 'Ouest')
        ],
        string="Orientation Jardin",
        default='north'
    )
