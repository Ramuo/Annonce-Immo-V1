{
    'name': 'Sponsor program',
    'summary': 'Track and manage user or partner sponsorships',
    'description': """
        A custom module to manage sponsoring and rewards user or partner:
        - Track sponsor
        - Assign points
        - Redeem rewards
        - Generate reports
    """,
    'version': '18.0.1.0.0',
    'category': 'Sales', 
    'author': 'Alpha',
    'website': 'http://www.odooalpha.com',
    'depends': ['base', 'sale_management', 'contacts', 'mail', 'crm'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        #Views
        'views/sponsorship_relationship_views.xml',
        'views/res_partner_views.xml',
        'views/sponsor_wizard_views.xml',
        'views/sponsorship_redemption_views.xml',
        'views/sponsorship_type_views.xml',
        'views/sponsorship_reward_type_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ], 
    
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}





