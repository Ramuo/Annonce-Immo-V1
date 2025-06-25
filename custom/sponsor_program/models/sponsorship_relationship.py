from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

from dateutil.relativedelta import relativedelta


class SponsorshipRelationship(models.Model):
    _name = 'sponsorship.relationship'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin'] 
    _description = 'Sponsorship Relation'
    _rec_name = 'display_name'
    _rec_name = 'sponsor_id'


    sponsor_id = fields.Many2one('res.partner', string="Parrain", required=True)
    sponsored_id = fields.Many2one('res.partner', string="Parrainé", required=True)
    datetime_created = fields.Datetime(string='Date de création', default=fields.Datetime.now, readonly=True)
    sponsor_email = fields.Char(related='sponsor_id.email', string="E-mail parrain", store=True)
    sponsored_email = fields.Char(related='sponsored_id.email', string="E-mail parrainé", store=True)
    sponsor_street = fields.Char(related="sponsor_id.street", string="Rue")
    sponsored_street = fields.Char(related="sponsored_id.street", string="Rue")
    sponsor_city = fields.Char(related="sponsor_id.city", string="Ville")
    sponsored_city = fields.Char(related="sponsored_id.city", string="Ville")

    description = fields.Text()
    sales_id = fields.Many2one('res.users', string="Vendeur")
    lead_id = fields.Many2one('crm.lead', string='Lead associé', readonly=True)
    # points_granted = fields.Boolean(string="Points attribués", default=False)
    points_awarded = fields.Integer(string="Points attribués", default=10)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('cancelled', 'Annulé'),
    ], default='draft', string="Statut")
    date_confirmed = fields.Datetime(string="Date de confirmation")



    display_name = fields.Char(string="Détails", compute='_compute_display_name', store=True)
    #Compute field for display_name
    @api.depends('sponsor_id', 'sponsored_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.sponsor_id.name} → {rec.sponsored_id.name}"
    
    # Constrains for sponsorship
    @api.constrains('sponsor_id', 'sponsored_id')
    def _check_unique_sponsorship(self):
        for rec in self:
            #Prevent self-sponsorship
            if rec.sponsor_id == rec.sponsored_id:
                raise ValidationError("Le parrain et le parrainé ne peuvent pas être la même personne.") 

            #Prevent duplicate sponsorships
            existing = self.search([
                ('sponsor_id', '=', rec.sponsor_id.id),
                ('sponsored_id', '=', rec.sponsored_id.id),
                ('id', '!=', rec.id)  # Exclude current record in update context
            ])
            if existing:
                raise ValidationError("Ce lien de parrainage existe déjà !")

            #Prevent reverse sponsorship (B sponsoring A if A already sponsored B)
            reverse = self.search([
                ('sponsor_id', '=', rec.sponsored_id.id),
                ('sponsored_id', '=', rec.sponsor_id.id)
            ])
            if reverse:
                raise ValidationError("Le parrainage inverse n'est pas autorisé")

    def action_confirm(self):
        for rel in self:
            rel.state = 'confirmed'
            rel.date_confirmed = fields.Datetime.now()

    def action_cancel(self):
        for rel in self:
            rel.state = 'cancelled'



    # Auto-create CRM lead when a sponsored person is added
    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if rec.sponsored_id:
            lead = self.env['crm.lead'].create({
                'name': f"Nouveau prospect parrainé: {rec.sponsored_id.name}",
                'partner_id': rec.sponsored_id.id,
                "contact_name": rec.sponsored_id.name,
                'email_from': rec.sponsored_id.email,
                'phone': rec.sponsored_id.phone or rec.sponsored_id.mobile,
                'description': f"Contact parrainé par {rec.sponsor_id.name}",
                # 'sponsor': rec.sponsored_id.email,
            })
            rec.lead_id = lead.id 
        return rec          
    


    ##################################FILTRE#################################################""""
    # Date for filtering and grouping
    date_created = fields.Date(string='Date (filtrage)', compute='_compute_date_only', store=True, index=True)

    is_this_month = fields.Boolean(compute='_compute_period_flags', store=True)
    is_last_month = fields.Boolean(compute='_compute_period_flags', store=True)
    is_last_3_months = fields.Boolean(compute='_compute_period_flags', store=True)
    is_this_year = fields.Boolean(compute='_compute_period_flags', store=True)
    is_last_year = fields.Boolean(compute='_compute_period_flags', store=True)

    @api.depends('datetime_created')
    def _compute_date_only(self):
        for rec in self:
            rec.date_created = rec.datetime_created.date() if rec.datetime_created else False

    @api.depends('date_created')
    def _compute_period_flags(self):
        today = fields.Date.context_today(self)
        first_day_this_month = today.replace(day=1)
        first_day_last_month = first_day_this_month - relativedelta(months=1)
        first_day_this_year = today.replace(month=1, day=1)
        first_day_last_year = first_day_this_year - relativedelta(years=1)

        for rec in self:
            rec_date = rec.date_created
            rec.is_this_month = rec_date >= first_day_this_month if rec_date else False
            rec.is_last_month = first_day_last_month <= rec_date < first_day_this_month if rec_date else False
            rec.is_last_3_months = rec_date >= today - relativedelta(months=3) if rec_date else False
            rec.is_this_year = rec_date >= first_day_this_year if rec_date else False
            rec.is_last_year = first_day_last_year <= rec_date < first_day_this_year if rec_date else False

    # Month-Year display label (e.g., "Janvier 2025")
    month_year_label = fields.Char(string="Mois + Année", compute='_compute_month_year_label', store=True, index=True)

    @api.depends('datetime_created')
    def _compute_month_year_label(self):
        import locale
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        except locale.Error:
            pass
        for rec in self:
            if rec.datetime_created:
                rec.month_year_label = rec.datetime_created.strftime('%B %Y').capitalize()
            else:
                rec.month_year_label = False

    # Optional: sorting key
    month_year_key = fields.Date(string="Clé de tri Mois+Année", compute='_compute_month_year_key', store=True)

    @api.depends('datetime_created')
    def _compute_month_year_key(self):
        for rec in self:
            if rec.datetime_created:
                rec.month_year_key = rec.datetime_created.replace(day=1).date()
            else:
                rec.month_year_key = False