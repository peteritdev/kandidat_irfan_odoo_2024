# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ConfirmWizardSale(models.TransientModel):
    _name = 'confirm.wizard.sale'
    _description = 'Checking Credit Limit Partner Perdivision'

    message_warning = fields.Char(string="WARNING", readonly=True)
    over_limit_message = fields.Char(string="Over Limit Message", readonly=True)
    over_limit_value = fields.Float(string="Over Limit Value", digits='Product Price', readonly=True)
    credit_limit_message = fields.Char(string="Credit Limit Message", readonly=True)
    credit_limit_value = fields.Float(string="Credit Limit Value", digits='Product Price', readonly=True)
    message_sale_overdue = fields.Char(string="Message Overdue", readonly=True)
    message = fields.Char(string="Message", readonly=True)

    def action_confirm(self):
        sale_order_id = self.env.context.get('active_id')
        sale_order = self.env['sale.order'].browse(sale_order_id)
        sale_order.with_context(skip_over_limit_check=True).sudo().action_confirm()
        return True
    
    def action_draft(self):
        sale_order_id = self.env.context.get('active_id')
        sale_order = self.env['sale.order'].browse(sale_order_id)
        sale_order.action_draft()
        return True