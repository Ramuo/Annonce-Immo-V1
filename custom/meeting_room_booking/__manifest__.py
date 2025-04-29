{
    'name': 'Meeting Room Booking',
    'version': '1.0.0',
    "sequence": 15,
    'summary': 'App to manage and book meeting rooms.',
    'description': """
        Manage meeting room, book schedules, and prevent double bookings.
    """,
    'author': 'Alpha',
    'website': "https://www.website.com",
    'category': 'Productivity',
    'depends': ['base',],
    'data': [
        'security/ir.model.access.csv',
        'views/room_view.xml',
        'views/booking_view.xml',
        'views/action.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}