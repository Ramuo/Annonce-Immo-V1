from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SponsorCreateSponsoredWizard(models.TransientModel):
    _name = 'sponsor.wizard.create.sponsored' 
    _description = 'Wizard to create Sponsor Contact'


    name = fields.Char(string='Nom', required=True)
    email = fields.Char(string='E-mail')
    phone = fields.Char(string='Téléphone')
    sponsor_id = fields.Many2one('res.partner', string='Parrainage')

    
    def action_create_contact(self):
        """Create a new contact if it doesn't already exist (based on email)."""
        contact = None

        # Search by email if provided
        if self.email:
            existing_contact = self.env['res.partner'].search([('email', '=', self.email)], limit=1)
            if existing_contact:
                raise ValidationError(f"Un contact avec l'e-mail '{self.email}' existe déjà : {existing_contact.name}")

        # If not found, create the contact
        if not contact:
            contact = self.env['res.partner'].create({
                'name': self.name,
                'email': self.email,
                'phone': self.phone,
                'customer_rank': 1  # Optional: marks as a customer
            })

        # Close the wizard
        return {'type': 'ir.actions.act_window_close'}
