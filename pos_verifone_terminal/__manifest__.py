# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "POS Verifone Terminal Integration",
    "version": "18.0.1.2.0",
    "category": "Point of Sale",
    "license": "AGPL-3",
    "summary": "Add support for Caisse-AP payment protocol used in France",
    "author": "Erik MR",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/l10n-france",
    "depends": ["point_of_sale"],
    "data": [
        "views/pos_payment_method.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_verifone_terminal/static/src/app/payment_verifone.esm.js",
            "pos_verifone_terminal/static/src/app/verifone_pos_patch.js",
            "pos_verifone_terminal/static/src/overrides/models/models.esm.js",
        ],
    },
    "installable": True,
}
