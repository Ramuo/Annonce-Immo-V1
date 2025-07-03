from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    sponsor_ids = fields.One2many('sponsorship.relationship','sponsor_id', string="Parrain")
    sponsored_ids = fields.One2many('sponsorship.relationship','sponsor_id', string="Parrainé")

    sponsored_count = fields.Integer(string='Total Filleuls', compute="_compute_sponsored_count")

    total_earned_points = fields.Integer(
        string="Total points gagnés", compute='_compute_total_earned_points', store=True, tracking=True
    )

    sponsorship_redemption_ids = fields.One2many(
        'sponsorship.redemption', 'sponsor_id', string="Récompenses"
    )

    total_redeemed_points = fields.Integer(
        string="Total points utilisés", compute='_compute_total_redeemed_points', store=True, tracking=True,
        help="Total des points consommés sur des récompenses approuvées."
    )

    available_points = fields.Integer(
        string="Points disponibles", compute="_compute_available_points", store=True, tracking=True,
        help="Points disponibles = gagnés - utilisés"
    )

    @api.depends('sponsored_ids')
    def _compute_sponsored_count(self):
        for rec in self:
            rec.sponsored_count = len(rec.sponsored_ids)

    @api.depends('sponsored_ids.points_awarded', 'sponsored_ids.state')
    def _compute_total_earned_points(self):
        for partner in self:
            partner.total_earned_points = sum(
                rel.points_awarded for rel in partner.sponsored_ids if rel.state == 'confirmed')

    @api.depends('sponsorship_redemption_ids.state', 'sponsorship_redemption_ids.required_points')
    def _compute_total_redeemed_points(self):
        for partner in self:
            partner.total_redeemed_points = sum(
                r.required_points for r in partner.sponsorship_redemption_ids if r.state == 'approved'
            )

    @api.depends('total_earned_points', 'total_redeemed_points')
    def _compute_available_points(self):
        for partner in self:
            partner.available_points = partner.total_earned_points - partner.total_redeemed_points


    """ @api.constrains('available_points')
    def _check_available_points_positive(self):
        for rec in self:
            if rec.available_points < 0:
                raise ValidationError(_("Les points disponibles ne peuvent pas être négatifs.")) """

##############################################################################################################

    # Action methods for contacts to view sponsored
    def action_open_sponsored_contacts(self):
        self.ensure_one()
        return{
            'type': 'ir.actions.act_window',
            'name': 'Parrainé',
            'res_model': 'sponsorship.relationship',
            'view_mode': 'list,form',
            'domain': [('sponsor_id', '=', self.id)],
            'context': {'default_sponsor_id': self.id}
        }

    # Action methods for contacts to view sponsor
    def action_open_sponsor_of(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Parrain',
            'res_model': 'sponsorship.relationship',
            'view_mode': 'list,form',
            'domain': [('sponsored_id', '=', self.id)],
            'context': {'default_sponsored_id': self.id}
        }
    

      