{
    "name": "POS Paymob",
    "version": "18.0.0.0",
    "author": "Paymob",
    "maintainer": "Paymob",
    "category": "Sales/Point of Sale",
    "sequence": 6,
    "summary": "Integrate your POS with an Paymob payment terminal",
    "description": "Odoo plugin for paymob pos first fintech company to receive the Central Bank of Egypt’s (CBE) Payments Facilitator license in 2018. We launched operations in Pakistan in 2021 and in the UAE in 2022. Paymob received Saudi Payments PTSP certification in May 2023 enabling us to launch operations in KSA. In December 2023 Paymob became the first international fintech company to receive Oman’s PSP",
    "data": [
        "views/res_config_settings_views.xml",
        "views/pos_payment_method_views.xml",
    ],
    "depends": ["point_of_sale"],
    "installable": True,
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_paymob/static/**/*",
        ],
    },
    "images": ["static/description/banner.jpg"],
    "license": "LGPL-3",
}
