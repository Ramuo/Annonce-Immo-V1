from odoo import fields, models, api




class AchievementType(models.Model):
    _name = 'achievement.type'
    _description = 'Achievement Type'

    name = fields.Char(string='Type Name', required=True)
    description = fields.Text(string='Description')