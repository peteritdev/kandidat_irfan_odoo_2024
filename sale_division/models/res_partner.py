# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    sale_division_ids = fields.One2many('sale.division.partner.line', 'partner_id', string="Divisi Penjualan")

class Partner(models.Model):
    _inherit = 'res.partner'

    # NOT A REAL PROPERTY !!!!
    property_product_pricelist = fields.Many2one(
        'product.pricelist', 'Pricelist', invisible=True)
    
    def _get_name(self):
        """ Utility method to allow name_get to be overrided without re-browse the partner """
        partner = self
        name = partner.name or ''

        if partner.company_name or partner.parent_id:
            if not name and partner.type in ['invoice', 'delivery', 'other']:
                name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
            if not partner.is_company:
                name = "%s" % (name)
        if self._context.get('show_address_only'):
            name = partner._display_address(without_company=True)
        if self._context.get('show_address'):
            name = name + "\n" + partner._display_address(without_company=True)
        name = name.replace('\n\n', '\n')
        name = name.replace('\n\n', '\n')
        if self._context.get('address_inline'):
            name = name.replace('\n', ', ')
        if self._context.get('show_email') and partner.email:
            name = "%s <%s>" % (name, partner.email)
        if self._context.get('html_format'):
            name = name.replace('\n', '<br/>')
        if self._context.get('show_vat') and partner.vat:
            name = "%s ‒ %s" % (name, partner.vat)
        return name

class SaleDivisionPartnerLane(models.Model):
    _name = 'sale.division.partner.line'
    _description = 'Sale Division Partner line'

    partner_id = fields.Many2one('res.partner', string='Proyek', required=True, ondelete='cascade')
    sale_division_id = fields.Many2one('sale.division', string="Divisi", required=True, tracking=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True, related='company_id.currency_id', store=True)
    credit_limit = fields.Monetary(string="kredit Limit", currency_field='currency_id', required=True, tracking=True)
    limit_used = fields.Monetary(string="Limit Terpakai", currency_field='currency_id', compute='_compute_limit_used')   
    remaining_limit = fields.Monetary(string="Sisa Limit", currency_field='currency_id', compute='_compute_remaining_limit')
    over_limit = fields.Monetary(string="Over Limit", currency_field='currency_id', compute='_compute_over_limit')

    @api.model
    def _compute_limit_used(self):
        for rec in self:
            sale_divisi = self.env['sale.order'].search([
                ('partner_id', '=', rec.partner_id.id),
                ('sale_division_id', '=', rec.sale_division_id.id),
                ('state', 'in', ('sale', 'done'))])
            if sale_divisi:
                rec.limit_used = sum(sale_divisi.mapped('amount_total'))
            else:
                rec.limit_used = False
    
    @api.model
    def _compute_remaining_limit(self):
        for rec in self:
            if rec.limit_used > 0 and rec.limit_used < rec.credit_limit:
                rec.remaining_limit = rec.credit_limit - rec.limit_used
            else:
                rec.remaining_limit = False
    
    @api.model
    def _compute_over_limit(self):
        for rec in self:
            if rec.limit_used > rec.credit_limit:
                rec.over_limit = rec.limit_used - rec.credit_limit
            else:
                rec.over_limit = False

    def action_view_sale_order(self):
        self.ensure_one()
        result = {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "domain": [('partner_id', '=', self.partner_id.id), ('sale_division_id', '=', self.sale_division_id.id), ('state', 'in', ('sale', 'done'))],
            "context": {"create": False},
            "name": "Sale Order",
            'view_mode': 'tree,form',
        }
        return result