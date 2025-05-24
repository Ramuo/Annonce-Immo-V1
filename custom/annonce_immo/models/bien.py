from odoo import models, fields, api

class Bien(models.Model):
    _name = "bien.immobilier"
    _description = "Annonce de Biens Immobiliers"

    name = fields.Char(string="Nom", required=True)
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('received', 'Offre réçus'),
        ('acepted', 'Offre accepté'),
        ('sold', 'Vendu'),
        ('cancel', 'Annulé'),
    ], default='new', string='Statut')
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
    offer_count = fields.Integer(string="Nbre Offre", compute="_compute_offer_count")

    # Computed field for total area
    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for rec in self :
            if rec.living_area and rec.garden_area:
                rec.total_erea = rec.living_area + rec.garden_area
            else:
                rec.total_erea = False
    
    # Action buttons to set an property state "accepted" 
    def action_sold(self):
        self.state = "sold"
    
    # Action button to set a property state "cancel"
    def action_cancel(self):
        self.state = "cancel"
   
    # Compute field for Offer_count
    @api.depends("offers_ids")
    def _compute_offer_count(self):
        for rec in self:
            rec.offer_count = len(rec.offers_ids) 
    

    # Action window smart button to shaw offers
    def action_property_view_offers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Offres',
            'res_model': 'offre.bien',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }
    

