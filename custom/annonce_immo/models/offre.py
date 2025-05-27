from odoo import fields, models, api
from datetime import timedelta
from odoo.exceptions import ValidationError




class OffreBien(models.Model):
    _name = 'offre.bien'
    _description = 'Offres des biens'




    name = fields.Char(string="Description", compute="_compute_name")
    price = fields.Float(string='Prix')
    status = fields.Selection([
        ('accepted', 'Accepté'),
        ('refused', 'Refusé'),
    ], string='Statut')
    partner_id = fields.Many2one('res.partner', string='Client')
    property_id = fields.Many2one('bien.immobilier', string='Bien')
    # creation_date = fields.Date(string='Date de création', default=fields.Date.today)
    validity = fields.Integer(string='Validité')
    deadline = fields.Date(string="Date d'échéance", compute='_computed_deadline', inverse='_inverse_deadline')
    partner_email = fields.Char(related="partner_id.email", string="Email")
    partner_phone = fields.Char(related="partner_id.phone", string="Téléphone")
    
    #Function to set a default create date
    @api.model
    def _set_create_date(self):
        return fields.Date.today()
    
    creation_date = fields.Date(string='Date de création', default=_set_create_date)

    # Computed field for deadline
    @api.depends('validity', 'creation_date')
    def _computed_deadline(self):
        for rec in self:
            if rec.creation_date and rec.validity:
                rec.deadline = rec.creation_date + timedelta(days=rec.validity)
            else:
                rec.deadline = False

    # inverse decoretor for deadline
    def _inverse_deadline(self):
        for rec in self:
            if rec.deadline and rec.validity:
                rec.validity = (rec.deadline - rec.creation_date).days
            else:
                rec.validity = False


     # Constraint decorator to avoid the field "validity" to have a negative value
    @api.constrains('validity')
    def _check_validity(self):
        for rec in self:
            if rec.deadline <= rec.creation_date:
                raise ValidationError("La date limite ne doit pas être inférieure à la date de création.")
    

    #Computed field for offer name
    @api.depends('property_id', 'partner_id')
    def _compute_name(self):
        for rec in self:
            if rec.property_id and rec.partner_id:
                rec.name = f"{rec.property_id.name} - {rec.partner_id.name}"
            else:
                rec.name = False



    #Action accept offer
    def action_accept_offer(self):
        self._validate_accepted_offer()
        if self.property_id:
            self.property_id.write({
                'selling_price': self.price,
                'state': "accepted"
            }) 
        self.status = "accepted"
    
    #To Validate accepted offer and avoid accepting more than one offer
    def _validate_accepted_offer(self):
        offer_ids = self.env['offre.bien'].search([
            ('property_id', '=', self.property_id.id),
            ('status', '=', 'accepted')
        ])
        if offer_ids:
            raise ValidationError("Vous avez déjà accepté un offre")

    #Action to refuse offer
    def action_refuse_offer(self):
        self.status = "refused"
        if all(self.property_id.offers_ids.mapped('status')):
            self.property_id.write({
                'selling_price': 0,
                'state': 'received'
            })