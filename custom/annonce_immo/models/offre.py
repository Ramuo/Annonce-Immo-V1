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

    validity = fields.Integer(string='Validité')
    deadline = fields.Date(string="Date d'échéance", compute='_computed_deadline', inverse='_inverse_deadline')
    creation_date = fields.Date(string='Date de création')
    partner_email = fields.Char(related="partner_id.email", string="Email")
    partner_phone = fields.Char(related="partner_id.phone", string="Téléphone")

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

