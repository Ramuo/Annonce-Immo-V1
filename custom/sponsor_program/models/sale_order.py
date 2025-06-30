from odoo import models, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _confirm_first_sale_and_sponsorship(self, order):
        partner = order.partner_id

        # Check if this is the first confirmed order for this partner
        previous_sales = self.env['sale.order'].search_count([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sale', 'done']),
            ('id', '!=', order.id)
        ])

        if previous_sales == 0:
            # Try to find an existing draft sponsorship for this partner
            sponsorship = self.env['sponsorship.relationship'].search([
                ('sponsored_id', '=', partner.id),
                ('state', '=', 'draft')
            ], limit=1)

            if sponsorship:
                sponsorship.action_confirm()
                sponsorship.message_post(body=_("Parrainage confirmé automatiquement suite à la première commande validée."))

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            self._confirm_first_sale_and_sponsorship(order)
        return res
