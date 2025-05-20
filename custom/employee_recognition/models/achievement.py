from odoo import fields, models, api
from odoo.exceptions import ValidationError



class EmployeeAchievement(models.Model):
    _name = 'employee.achievement'
    _description = "Employee Achievement model"



    name = fields.Char(string="Achievement", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, ondelete='cascade')
    type_id = fields.Many2one(
        'achievement.type', 
        string="Achievement Type",
        required= True,
        default=lambda self: self.env['achievement.type'].search([], limit=1)
    )
    points = fields.Integer(string='Points', required=True)
    state =fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved')
    ], default="draft", string="State", required=True)
    date_awarded = fields.Date(string='Date Awarded', default=fields.Date.today, required=True)


    @api.constrains('points')
    def _check_points(self):
        for rec in self:
            if rec.points < 0 or rec.points > 100:
                raise ValidationError("Points must be between 0 and 100.")
    
    # To handle approve achievement in footer button
    def approve_achievement(self):
        for rec in self:
            if rec.state == 'approved':
                rec.write({'state': 'approved'})

    def reset_to_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

