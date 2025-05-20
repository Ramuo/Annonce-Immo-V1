{
    'name': 'Employee Recognition and Rewards',
    'summary': 'Track and reward employee achievements.',
    'description': """
        A custom module to manage employee recognition and rewards:
        - Track achievements
        - Assign points
        - Redeem rewards
        - Generate reports
    """,
    'version': '18.0.1.0.0',
    'category': 'Human Resources', 
    'author': 'Alpha',
    'website': 'http://www.odooalpha.com',
    'depends': ['base', 'hr',],
    'data': [
        "security/ir.model.access.csv",
        "views/achievement_view.xml",
        "views/achievement_type_view.xml",
        "views/reward_view.xml",
        "views/actions.xml",
        "views/menus.xml",
    ],
    
    
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}