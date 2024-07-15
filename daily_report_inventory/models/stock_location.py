# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Location(models.Model):
    _inherit = "stock.location"
    _description = "Inventory Locations"

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", tracking=True)