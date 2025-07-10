from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)



class SponsorshipRedemption(models.Model):
    _name = 'sponsorship.redemption'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sponsorship Points Redemption'
    _order = 'date desc'

    name = fields.Char(string="Nom", compute='_compute_name', store=True)
    sponsor_id = fields.Many2one('res.partner', string='Parrain', required=True)
    sponsored_id = fields.Many2one('res.partner', string='Filleul')
    date = fields.Datetime(default=fields.Datetime.now, readonly=True, string="Date de création")
    required_points = fields.Integer(string="Points", required=True, tracking=True, readonly=True)
    state = fields.Selection([
        ('pending', 'En attente'),
        ('approved', 'Approuvée'),
        ('rejected', 'Rejetée'),
    ], string="Statut", default='pending', tracking=True)
    approver_id = fields.Many2one('res.users', string='Approuver par', tracking=True)
    approval_date = fields.Datetime(string="Date d'approbation", tracking=True)
    sponsorship_id = fields.Many2one('sponsorship.relationship', string="Description", ondelete='set null')
    #To add the smart buttons in sponsorship.redemption
    sponsored_count = fields.Integer(related='sponsor_id.sponsored_count', string='Total Filleuls')
    total_earned_points = fields.Integer(related='sponsor_id.total_earned_points', string='Points gagnés', readonly=True)
    total_redeemed_points = fields.Integer(related='sponsor_id.total_redeemed_points', string='Points utilisés', readonly=True)
    available_points = fields.Integer(related='sponsor_id.available_points', string='Points disponibles', readonly=True)
    #To Add the smart button for sponsored sale order
    sale_order_count = fields.Integer(string="Commandes Filleul", compute="_compute_sale_order_count")
    #add type de recompense in sponsorship.redemption 
    sponsorship_reward_type_id = fields.Many2one('sponsorship.reward.type', string="Type de récompense")
    #Add field to show if notification is sent to the sponsor after approval
    notification_sent = fields.Boolean(string="Notification envoyée", default=False, readonly=True)

    #Compute field for display_name
    @api.depends('sponsor_id')
    def _compute_name(self):
        for rec in self:
            sponsor_name = rec.sponsor_id.name or ""
            rec.name = f"{sponsor_name}"

    #Compute sale order count for sponsored
    def _compute_sale_order_count(self):
        for rec in self:
            if rec.sponsored_id:
                rec.sale_order_count = self.env['sale.order'].search_count([
                    ('partner_id', '=', rec.sponsored_id.id),
                    ('state', 'in', ['sale', 'done'])
                ])
            else:
                rec.sale_order_count = 0

    #To create redemption
    @api.model
    def create(self, vals):
        return super().create(vals)

    #To approve redemption
    def action_approve(self):
        for record in self:
            if record.required_points < 10:
                raise ValidationError(_("Le nombre de points minimum doit être 10."))

            if record.state != 'pending':
                raise ValidationError(_("Seules les demandes en attente peuvent être approuvées."))

            sponsor = record.sponsor_id
            current_available = sponsor.total_earned_points - sponsor.total_redeemed_points
            if current_available < record.required_points:
                raise ValidationError(_(
                    "Points insuffisants. %s a %s disponibles, mais %s sont requis."
                ) % (sponsor.name, current_available, record.required_points))

            record.write({
                'state': 'approved', 
                'approver_id': self.env.user.id,
                'approval_date': datetime.now(),
            })

            record.message_post(body=_("Approbation : %s points validés pour %s.") %
                                (record.required_points, sponsor.name))

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    #To reject redemption
    def action_reject(self):
        for record in self:
            record.state = 'rejected'
            record.message_post(body=_("La demande de récompense a été rejetée, il faut retirer les points dans “Parrainer”"))
        

    def write(self, vals):
        for record in self:
            old_state = record.state
            new_state = vals.get('state', old_state)
            old_points = record.required_points
            new_points = vals.get('required_points', old_points)

            record._handle_points_change(old_state, new_state, old_points, new_points)

        return super().write(vals)

    def _handle_points_change(self, old_state, new_state, old_points, new_points):
        sponsor = self.sponsor_id

        if old_state == 'approved' and new_points != old_points:
            raise ValidationError(_("Impossible de modifier les points après approbation."))

        if old_state != 'approved' and new_state == 'approved':
            current_available = sponsor.total_earned_points - sponsor.total_redeemed_points
            if current_available < new_points:
                raise ValidationError(_(
                    "Points insuffisants pour approbation. %s a %s disponibles, %s requis."
                ) % (sponsor.name, current_available, new_points))

    #To delete redemption
    def unlink(self):
        for record in self:
            if record.state == 'approved':
                raise ValidationError(_("Une récompense approuvée ne peut pas être supprimée."))
            elif record.state == 'pending':
                raise ValidationError(_("Cette récompense est en attente d'approbation et ne peut pas être supprimée. Veuillez d'abord la rejeter."))
            elif record.state == 'rejected':
                _logger.info("Suppression de la récompense rejetée : %s", record.id)
        return super().unlink()
    
    #Smart buttons Actions
    def open_sponsored_partners(self):
        return{
            'type': 'ir.actions.act_window',
            'name': _('Filleuls'),
            'res_model': 'sponsorship.relationship',
            'view_mode': 'list,form',
            'domain': [('sponsor_id', '=', self.sponsor_id.id)]
        }
    
    def open_earned_points(self):
        return self.open_sponsored_partners()
    
    def open_redeemed_points(self):
        return{
            'type': 'ir.actions.act_window',
            'name': _('Récompenses utilisées'),
            'res_model': 'sponsorship.redemption',
            'view_mode': 'list,form',
            'domain': [('sponsor_id', '=', self.sponsor_id.id), ('state', '=', 'approved')],
        }

    def open_available_points(self):
        return{
            'type': 'ir.actions.act_window',
            'name': _('Récompenses'),
            'res_model': 'sponsorship.redemption',
            'view_mode': 'list,form',
            'domain': [('sponsor_id', '=', self.sponsor_id.id)],
        }
    #Smart button action to show sponsored order
    def action_view_sponsored_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Commandes du filleul'),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.sponsored_id.id)],
            'context': {'default_partner_id': self.sponsored_id.id},
        }
    
    #Action to send approval notification email to sponsor
    def action_send_approval_notification(self):
        self.ensure_one()

        if self.notification_sent:
            raise ValidationError(_("La notification a déjà été envoyée."))

        if self.state != 'approved':
            raise ValidationError(_("La notification ne peut être envoyée que si la récompense est approuvée."))

        if not self.sponsor_id or not self.sponsor_id.email or not self.sponsor_id.email.strip():
            raise ValidationError(_("Le parrain n'a pas d'adresse email valide."))

        template = self.env.ref('sponsor_program.mail_template_sponsorship_redemption_approved', raise_if_not_found=False)
        if not template:
            raise ValidationError(_("Le modèle d'email est introuvable."))

        # Sujet personnalisé sécurisé sans retour à la ligne
        raw_subject = f"🎉 Félicitations {self.sponsor_id.name} — votre récompense est approuvée !"
        clean_subject = raw_subject.replace('\n', ' ').replace('\r', '')

        email_values = {
            'email_to': self.sponsor_id.email.strip(),
            'email_from': self.env.user.email_formatted,
            'subject': clean_subject,
        }

        print(email_values)

        template.send_mail(self.id, force_send=True, email_values=email_values)

        self.write({'notification_sent': True})
        self.message_post(body=_("Notification envoyée à %s.") % self.sponsor_id.name)


   
    