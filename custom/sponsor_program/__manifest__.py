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
    'depends': ['base', 'sale_management', 'contacts', 'mail'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'views/sponsorship_relationship_views.xml',
        'views/res_partner_views.xml',
        'views/sponsor_wizard_views.xml',
        'views/actions.xml',
        'views/menus.xml',
    ], 
    
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}