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
    reason = fields.Char(string='Raison')
    state = fields.Selection([
        ('pending', 'En attente'),
        ('approved', 'Approuvée'),
        ('rejected', 'Rejetée'),
    ], default='pending', tracking=True)
    approver_id = fields.Many2one('res.users', string='Approuver par', tracking=True)
    approval_date = fields.Datetime(string="Date d'approbation", readonly=True, tracking=True)
    sponsorship_id = fields.Many2one('sponsorship.relationship', string="Description", ondelete='set null')
    #To add the smart buttons in sponsorship.redemption
    sponsored_count = fields.Integer(related='sponsor_id.sponsored_count', string='Nombre parrainés')
    total_earned_points = fields.Integer(related='sponsor_id.total_earned_points', string='Points gagnés', readonly=True)
    total_redeemed_points = fields.Integer(related='sponsor_id.total_redeemed_points', string='Points utilisés', readonly=True)
    available_points = fields.Integer(related='sponsor_id.available_points', string='Points disponibles', readonly=True)
    #To Add the smart button for sponsored sale order
    sale_order_count = fields.Integer(string="Commandes Filleul", compute="_compute_sale_order_count")

    sponsorship_reward_type_id = fields.Many2one('sponsorship.reward.type', string="Type de récompense", required=True)
    

    #Compute field for display_name
    @api.depends('sponsor_id')
    def _compute_name(self):
        for rec in self:
            sponsor_name = rec.sponsor_id.name or ""
            rec.name = f"{sponsor_name}"

    #Compute sale order count for sponsored
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = self.env['sale.order'].search_count([
                ('partner_id', '=', rec.sponsored_id.id),
                ('state', 'in', ['sale', 'done'])
        ])

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
    #####################Action submit for approval##########################
    def action_submit_for_approval(self):
        for record in self:
            """ if record.state != 'draft':
                raise ValidationError(_("Cette demande a déjà été soumise ou traitée."))
            record.state = 'pending' """

            manager = self.env['res.users'].search([('email', '=', 'alpha.barry88@laposte.net')], limit=1)
            if not manager:
                manager = self.env.ref('base.user_admin') or self.env.user
                record.message_post(body=_("Alpha introuvable. Approbateur par défaut : %s.") % manager.name)

            record.approver_id = manager
            record.message_post(body=_("Demande soumise pour approbation à %s.") % manager.name)

            record.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=manager.id,
                summary=_("Approuver une récompense"),
                note=_("%s veut la récompense de ses %s points.") % (record.sponsor_id.name, record.required_points),
            )

            template = self.env.ref('sponsor_program.mail_template_redemption_approval', raise_if_not_found=False)
            if template:
                template.send_mail(record.id, force_send=True)