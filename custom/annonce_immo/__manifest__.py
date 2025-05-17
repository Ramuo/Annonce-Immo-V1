{
    "name": "Annonce Immo",
    "version": "1.0.0",
    "summary": "Annonce Immobilière",
    "sequence": 5,
    "description": """
        Module d'annonces immobilières pour afficher les biens disponibles.
    """,
    "author": "Alpha",
    "company": "Miandano",
    "website": "https://www.website.com",
    "category": "Sales",
    "depends": ['base'],
    "data": [
        #Security
        'security/ir.model.access.csv',
        #Views
        'views/bien_view.xml',
        'views/type_bien_view.xml',
        'views/particularite_view.xml',
        'views/actions.xml',
        'views/menu.xml',

        # Data File
        'data/type_bien.xml',

        # Demo file
        'demo/particularite_bien.xml',
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
