from odoo import api, fields, models, _

class SaleDivision(models.Model):
    _name = 'sale.division'
    _description = 'Sale Division'

    name = fields.Char(string='Name', required=True, tracking=True, copy=False)
    note = fields.Char(string='Keterangan', tracking=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True, related='company_id.currency_id', store=True)
    price_list_id = fields.Many2one('product.pricelist', string='Price list', tracking=True)
    
    