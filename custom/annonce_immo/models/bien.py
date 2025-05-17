from odoo import models, fields, api

class Bien(models.Model):
    _name = "bien.immobilier"
    _description = "Annonce de Biens Immobiliers"

    name = fields.Char(string="Nom", required=True)
    particularite_ids = fields.Many2many('particularite.bien', string='Particularité')
    type_id = fields.Many2one('type.bien', string='Type de bien')
    description = fields.Text(string="Description")
    postcode = fields.Char(string="Code Postal")
    date_availability = fields.Date(string="Disponible Le")
    expected_price = fields.Float(string="Prix Attendu")
    best_offer = fields.Float(string="Meilleure Offre")
    selling_price = fields.Float(string="Prix de Vente")
    bedrooms = fields.Integer(string="Chambres")
    living_area = fields.Integer(string="Salon (m²)")
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
    offers_ids = fields.One2many('offre.bien', 'property_id', string='Offres')
    sales_id = fields.Many2one('res.users', string='Vendeur')
    buyer_id = fields.Many2one('res.partner', string="Acheteur")
    total_erea = fields.Integer(string='Surface Total', compute='_compute_total_area')
    phone = fields.Char(related="buyer_id.phone", string="Téléphone")
    

    # Computed field for total area
    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for rec in self :
            if rec.living_area and rec.garden_area:
                rec.total_erea = rec.living_area + rec.garden_area
            else:
                rec.total_erea = False
    
    

   