from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class SponsorshipRelationship(models.Model):
    _name = 'sponsorship.relationship'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin'] 
    _description = 'Sponsorship Relation'
    _rec_name = 'display_name'
    _rec_name = 'sponsor_id'


    display_name = fields.Char(string="Nom", compute='_compute_display_name', store=True) 
    sponsor_id = fields.Many2one('res.partner', string="Parrain", required=True)
    sponsored_id = fields.Many2one('res.partner', string="Filleul", required=True)
    datetime_created = fields.Datetime(string='Date de création', default=fields.Datetime.now, readonly=True)
    sponsor_email = fields.Char(related='sponsor_id.email', string="E-mail parrain", store=True)
    sponsored_email = fields.Char(related='sponsored_id.email', string="E-mail filleul", store=True)
   
    description = fields.Text()
    sales_id = fields.Many2one('res.users', string="Vendeur")
    lead_id = fields.Many2one('crm.lead', string='Lead associé', readonly=True)
    points_awarded = fields.Integer(string="Points attribués", default=10)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('cancelled', 'Annulé'),
    ], default='draft', string="Statut")
    date_confirmed = fields.Datetime(string="Date de confirmation")
    redemption_ids = fields.One2many('sponsorship.redemption', 'sponsorship_id', string="Récompense liée")
    #To show reward state in sponsorship.relationship
    reward_id = fields.Many2one('sponsorship.redemption', string="Récompense")
    reward_state = fields.Selection(related='reward_id.state', string="État de la récompense", store=True, readonly=True)
    #To show sponsored order via smart button in sponsorship.relationship
    sale_order_count = fields.Integer(string="Commandes Filleul", compute="_compute_sale_order_count")

    type_parrainage_id = fields.Many2one('sponsorship.type', string='Type de parrainage')

    
    #Compute field for display_name
    @api.depends('sponsor_id', 'sponsored_id')
    def _compute_display_name(self):
        for rec in self:
            sponsor_name = rec.sponsor_id.name or ""
            sponsored_name = rec.sponsored_id.name or ""
            rec.display_name = f"{sponsor_name} → {sponsored_name}"

    # Compute for sale order count
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = self.env['sale.order'].search_count([
                ('partner_id', '=', rec.sponsored_id.id),
                ('state', 'in', ['sale', 'done'])
            ])
    
    # Constrains for sponsorship
    @api.constrains('sponsor_id', 'sponsored_id')
    def _check_unique_sponsorship(self):
        for rec in self:
            # Auto-parrainage
            if rec.sponsor_id == rec.sponsored_id:
                raise ValidationError("Le parrain et le parrainé ne peuvent pas être la même personne.") 

            # Le filleul a déjà été parrainé par quelqu'un d'autre
            duplicate_filleul = self.search([
                ('sponsored_id', '=', rec.sponsored_id.id),
                ('id', '!=', rec.id)
            ])
            if duplicate_filleul:
                raise ValidationError(
                    _("Ce contact a déjà été parrainé par %s.") % duplicate_filleul[0].sponsor_id.name
                )

            # Lien exact déjà existant
            existing = self.search([
                ('sponsor_id', '=', rec.sponsor_id.id),
                ('sponsored_id', '=', rec.sponsored_id.id),
                ('id', '!=', rec.id)
            ])
            if existing:
                raise ValidationError("Ce lien de parrainage existe déjà !")

            # Parrainage croisé (A parrainé B et B essaie de parrainer A)
            reverse = self.search([
                ('sponsor_id', '=', rec.sponsored_id.id),
                ('sponsored_id', '=', rec.sponsor_id.id)
            ])
            if reverse:
                raise ValidationError("Le parrainage inverse n'est pas autorisé.")

    def action_confirm(self):
        for rel in self:
            # To prevent confirmation of points awarded is <= 0
            if rel.points_awarded <= 0 or rel.points_awarded > 100:
                raise ValidationError(_("Les points attribués doivent être différents de zéro, strictement positifs et inférieur à 100 pour confirmer ce parrainage."))
            
            # If state is not confirmed, set it to confirm
            if rel.state != 'confirmed':
                rel.state = 'confirmed'
                rel.date_confirmed = fields.Datetime.now()

                # To Check if a linked reward already exists
                existing_redemption = self.env['sponsorship.redemption'].search([
                    ('sponsorship_id', '=', rel.id)
                ], limit=1)

                # Create a linked reward already if it does not exist
                if not existing_redemption:
                    reward = self.env['sponsorship.redemption'].create({
                        'sponsor_id': rel.sponsor_id.id,
                        'sponsored_id': rel.sponsored_id.id,  
                        'required_points': rel.points_awarded,
                        'reason': _('Récompense en attente pour le parrainage de %s') % rel.sponsored_id.name,
                        'state': 'pending',  
                        'sponsorship_id': rel.id,
                    })
                    rel.reward_id = reward.id

    #To Cancel sponsorship
    def action_cancel(self):
        for rel in self:
            # Vérifier s'il existe une récompense approuvée liée à ce parrainage
            has_approved_redemption = self.env['sponsorship.redemption'].search_count([
                ('sponsorship_id', '=', rel.id),
                ('state', '=', 'approved')
            ]) > 0

            if has_approved_redemption:
                raise ValidationError(_("Impossible d'annuler ce parrainage : une récompense a été approuvée pour ce parrainage."))

            # Rejeter automatiquement la récompense associée en attente
            pending_redemption = self.env['sponsorship.redemption'].search([
                ('sponsorship_id', '=', rel.id),
                ('state', '=', 'pending')
            ], limit=1)

            if pending_redemption:
                pending_redemption.state = 'rejected'
                pending_redemption.message_post(body=_("Récompense rejetée automatiquement suite à l'annulation du parrainage."))

            rel.points_awarded = 0
            rel.state = 'cancelled'
            rel.message_post(body=_("Parrainage annulé. Points remis à zéro. Récompense associée rejetée si existante."))

    # To set in draft
    def action_draft(self):
        for record in self:
            record.state = 'draft'

    #To delete Sponsorship
    def unlink(self):
        for record in self:
            has_approved_redemption = self.env['sponsorship.redemption'].search_count([
                ('sponsorship_id', '=', record.id),
                ('state', '=', 'approved')
            ]) > 0

            if record.state == 'confirmed' and has_approved_redemption:
                raise ValidationError(_("Ce parrainage ne peut pas être supprimé car une récompense approuvée a été générée."))

            if record.state == 'confirmed':
                raise ValidationError(_("Impossible de supprimer le parrainage confirmé entre %s et %s. Il faut d'abord l'annuler.") %
                                    (record.sponsor_id.name, record.sponsored_id.name))

            if record.state in ('draft', 'cancelled'):
                _logger.info("Suppression du parrainage (%s) entre %s et %s", record.state, record.sponsor_id.name, record.sponsored_id.name)

                #Supprimer les récompenses associées en attente ou rejetées
                self.env['sponsorship.redemption'].search([
                    ('sponsorship_id', '=', record.id),
                    ('state', 'in', ['pending', 'rejected'])
                ]).unlink()

        return super().unlink()

    # Auto-create lead in CRM, when a sponsored a new person is added and if does not exist
    @api.model
    def create(self, vals):
        rec = super().create(vals)

        if rec.sponsored_id and rec.sponsored_id.email:
            existing_lead = self.env['crm.lead'].search([
                ('email_from', '=', rec.sponsored_id.email)
            ], limit=1)

            if not existing_lead:
                lead = self.env['crm.lead'].create({
                    'name': f"Nouveau prospect parrainé: {rec.sponsored_id.name}",
                    'partner_id': rec.sponsored_id.id,
                    'contact_name': rec.sponsored_id.name,
                    'email_from': rec.sponsored_id.email,
                    'phone': rec.sponsored_id.phone or rec.sponsored_id.mobile,
                    'description': f"Contact parrainé par {rec.sponsor_id.name}",
                })
                rec.lead_id = lead.id
            else:
                rec.message_post(body=_("Un prospect existe déjà avec l’email %s, aucun nouveau lead créé.") % rec.sponsored_id.email)
        return rec
       
    
    #Smart button action to show sponsored order
    def action_view_sponsored_orders(self):
        self.ensure_one()
        return {
            'name': _('Commandes du filleul'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.sponsored_id.id)],
            'context': {'default_partner_id': self.sponsored_id.id},
        }


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