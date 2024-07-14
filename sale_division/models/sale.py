# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = "Sales Order"

    
    
    sale_division_id = fields.Many2one('sale.division', string="Divisi", required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', 
                                    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('sale_division_ids.sale_division_id', '=', sale_division_id)]",)
    partner_shipping_id = fields.Many2one(
        'res.partner', readonly=True, required=True, invisible=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), '|', ('id', '=', partner_id), ('parent_id', '=', partner_id)]")
    pickup_method = fields.Selection(string='Pickup Method',
        selection=[('delivery', 'Delivery'), ('take_in_plant', 'Take in Plant')], required=True, tracking=True)

    @api.onchange('partner_id', 'sale_division_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            'pricelist_id': self.sale_division_id.price_list_id and self.sale_division_id.price_list_id.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': False,
            'user_id': partner_user.id or self.env.uid
        }
        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms

        # Use team of salesman if any otherwise leave as-is
        values['team_id'] = partner_user.team_id.id if partner_user and partner_user.team_id else self.team_id
        self.update(values)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('sale.order') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            divisi = self.env['sale.division'].browse(vals.get('sale_division_id'))        
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = False
            vals['pricelist_id'] = vals.setdefault('pricelist_id', divisi.price_list_id and divisi.price_list_id.id)
        result = super(SaleOrder, self).create(vals)
        return result
    
    # def action_confirm(self):
    #         # Kondisi untuk mengeluarkan wizard
    #     if self.env.context.get('skip_over_limit_check'):
    #         return super(SaleOrder, self).action_confirm()
    #     for rec in self:
    #         current_datetime = fields.Datetime.now()
    #         sale_divisi = self.env['sale.order'].search([('partner_id', '=', rec.partner_id.id), ('sale_division_id', '=', rec.sale_division_id.id), ('state', '!=', 'cancel')])
    #         date_overdue = self.env['sale.order'].search([('partner_id', '=', rec.partner_id.id), ('validity_date', '<', current_datetime), ('state', '=', 'draft')])
    #         sale_date_overdue = len(date_overdue)
    #         credit_limit = rec.partner_id.sale_division_ids.filtered(lambda r: r.sale_division_id == rec.sale_division_id).credit_limit
    #         amount_total = sum(sale_divisi.mapped('amount_total'))
    #         if amount_total > credit_limit and sale_date_overdue > 0:  
    #             return {
    #                 'name': _('Confirm Sale Order'),
    #                 'type': 'ir.actions.act_window',
    #                 'res_model': 'confirm.wizard.sale',
    #                 'view_mode': 'form',
    #                 'target': 'new',
    #                 'context': {
    #                     'default_message_warning': _('WARNING'),
    #                     'default_over_limit_message': _('Kredit limit anda telah melampaui batas sebesar:'),
    #                     'default_over_limit_value': amount_total-credit_limit,
    #                     'default_credit_limit_message': _('Sedangkan Limit andanya hanya sebesar:'),
    #                     'default_credit_limit_value': credit_limit,
    #                     'default_message_sale_overdue': _('Ada Transaksi Yang Terlambat'),
    #                     'default_message': _('Apakah Anda akan tetap melanjutkannya? Jika YA Tekan confirm Jika TIDAK tekan cancel'),
    #                     'active_id': rec.id,
    #                     'active_model': 'sale.order',
    #                 },
    #             }
    #         else:
    #             return super(SaleOrder, rec).action_confirm()
    #         if amount_total > credit_limit:  
    #             return {
    #                 'name': _('Confirm Sale Order'),
    #                 'type': 'ir.actions.act_window',
    #                 'res_model': 'confirm.wizard.sale',
    #                 'view_mode': 'form',
    #                 'target': 'new',
    #                 'context': {
    #                     'default_message_warning': _('WARNING'),
    #                     'default_over_limit_message': _('Kredit limit anda telah melampaui batas sebesar:'),
    #                     'default_over_limit_value': amount_total-credit_limit,
    #                     'default_credit_limit_message': _('Sedangkan Limit andanya hanya sebesar:'),
    #                     'default_credit_limit_value': credit_limit,
    #                     'default_message': _('Apakah Anda akan tetap melanjutkannya? Jika YA Tekan confirm Jika TIDAK tekan cancel'),
    #                     'active_id': rec.id,
    #                     'active_model': 'sale.order',
    #                 },
    #             }
    #         else:
    #             return super(SaleOrder, rec).action_confirm()
    #         if sale_date_overdue > 0:  
    #             return {
    #                 'name': _('Confirm Sale Order Overdue'),
    #                 'type': 'ir.actions.act_window',
    #                 'res_model': 'confirm.wizard.overdue',
    #                 'view_mode': 'form',
    #                 'target': 'new',
    #                 'context': {
    #                     'default_message_warning': _('WARNING'),
    #                     'default_message_sale_overdue': _('Ada Transaksi Yang Terlambat'),
    #                     'default_message': _('Apakah Anda akan tetap melanjutkannya? Jika YA Tekan confirm Jika TIDAK tekan cancel'),
    #                     'active_id': rec.id,
    #                     'active_model': 'sale.order',
    #                 },
    #             }
    #         else:
    #             return super(SaleOrder, rec).action_confirm()
    
    def action_confirm(self):
        if self.env.context.get('skip_over_limit_check'):
            return super(SaleOrder, self).action_confirm()

        for rec in self:
            current_datetime = fields.Datetime.now()
            sale_divisi = self.env['sale.order'].search([
                ('partner_id', '=', rec.partner_id.id),
                ('sale_division_id', '=', rec.sale_division_id.id),
                ('state', '!=', 'cancel')])
            date_overdue = self.env['sale.order'].search([
                ('partner_id', '=', rec.partner_id.id),
                ('validity_date', '<', current_datetime),
                ('state', '=', 'draft')])
            sale_date_overdue = len(date_overdue)
            credit_limit = rec.partner_id.sale_division_ids.filtered(lambda r: r.sale_division_id == rec.sale_division_id).credit_limit
            amount_total = sum(sale_divisi.mapped('amount_total'))

            if amount_total > credit_limit and sale_date_overdue > 0:
                wizard_model = 'confirm.wizard.sale'
                wizard_name = _('Confirm Sale Order')
                context = {
                    'default_message_warning': _('WARNING'),
                    'default_over_limit_message': _('Kredit limit anda telah melampaui batas sebesar:'),
                    'default_over_limit_value': amount_total - credit_limit,
                    'default_credit_limit_message': _('Sedangkan Limit andanya hanya sebesar:'),
                    'default_credit_limit_value': credit_limit,
                    'default_message_sale_overdue': _('Transaksi Yang Terlambat'),
                    'default_message': _('Apakah Anda akan tetap melanjutkannya? Jika YA Tekan confirm Jika TIDAK tekan cancel'),
                }

            elif amount_total > credit_limit:
                wizard_model = 'confirm.wizard.sale'
                wizard_name = _('Confirm Sale Order')
                context = {
                    'default_message_warning': _('WARNING'),
                    'default_over_limit_message': _('Kredit limit anda telah melampaui batas sebesar:'),
                    'default_over_limit_value': amount_total - credit_limit,
                    'default_credit_limit_message': _('Sedangkan Limit andanya hanya sebesar:'),
                    'default_credit_limit_value': credit_limit,
                    'default_message': _('Apakah Anda akan tetap melanjutkannya? Jika YA Tekan confirm Jika TIDAK tekan cancel'),
                }

            elif sale_date_overdue > 0:
                wizard_model = 'confirm.wizard.sale.overdue'
                wizard_name = _('Confirm Sale Order Overdue')
                context = {
                    'default_message_warning': _('WARNING'),
                    'default_message_sale_overdue': _('Transaksi Yang Terlambat'),
                    'default_message': _('Apakah Anda akan tetap melanjutkannya? Jika YA Tekan confirm Jika TIDAK tekan cancel'),
                }
            else:
                return super(SaleOrder, rec).action_confirm()

            return {
                'name': wizard_name,
                'type': 'ir.actions.act_window',
                'res_model': wizard_model,
                'view_mode': 'form',
                'target': 'new',
                'context': dict(context, active_id=rec.id, active_model='sale.order'),
            }

        return super(SaleOrder, self).action_confirm()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sales Order Line'

    sale_division_id = fields.Many2one('sale.division', string="Divisi", required=True, tracking=True)
    product_id = fields.Many2one(
        'product.product', string='Product', 
        domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id), ('sale_division_id', '=', sale_division_id)]",
        change_default=True, ondelete='restrict', check_company=True)
    pickup_method = fields.Selection(string='Pickup Method',
        selection=[('delivery', 'Delivery'), ('take_in_plant', 'Take in Plant')], related='order_id.pickup_method')
    take_in_plant = fields.Float(string="Potongan Harga", digits='Product Price', compute='_amount_take_in_plant', 
                    attrs={'invisible': [('pickup_method', '=', 'delivery')]}, help="Potongan Harga Untuk Produk yang di ambil langsung di plant.")

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'take_in_plant')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            if line.pickup_method == 'take_in_plant':
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'] - line.take_in_plant,
                    'price_subtotal': taxes['total_excluded'] - line.take_in_plant,
                })
            else:
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'] + line.take_in_plant,
                    'price_subtotal': taxes['total_excluded'] + line.take_in_plant,
                })

    @api.depends('product_id', 'pickup_method')
    def _amount_take_in_plant(self):
        """
        Compute the take_in_plant.
        """
        for order in self:
            if order.product_id.take_in_plant > 0 and order.pickup_method == 'take_in_plant':
                order.take_in_plant = order.product_id.take_in_plant
            else:
                order.take_in_plant = False

   