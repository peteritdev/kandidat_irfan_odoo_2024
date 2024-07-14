# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Location(models.Model):
    _inherit = "stock.location"
    _description = "Inventory Locations"

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", tracking=True)

class Warehouse(models.Model):
    _inherit = "stock.warehouse"
    _description = "Warehouse"
    
    def _get_locations_values(self, vals, code=False):
        """ Update the warehouse locations. """
        def_values = self.default_get(['reception_steps', 'delivery_steps'])
        reception_steps = vals.get('reception_steps', def_values['reception_steps'])
        delivery_steps = vals.get('delivery_steps', def_values['delivery_steps'])
        code = vals.get('code') or code
        code = code.replace(' ', '').upper()
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        sub_locations = {
            'lot_stock_id': {
                'name': _('Stock'),
                'active': True,
                'usage': 'internal',
                'barcode': self._valid_barcode(code + '-STOCK', company_id),
                'warehouse_id': self.id
            },
            'wh_input_stock_loc_id': {
                'name': _('Input'),
                'active': reception_steps != 'one_step',
                'usage': 'internal',
                'barcode': self._valid_barcode(code + '-INPUT', company_id),
                'warehouse_id': self.id
            },
            'wh_qc_stock_loc_id': {
                'name': _('Quality Control'),
                'active': reception_steps == 'three_steps',
                'usage': 'internal',
                'barcode': self._valid_barcode(code + '-QUALITY', company_id),
                'warehouse_id': self.id
            },
            'wh_output_stock_loc_id': {
                'name': _('Output'),
                'active': delivery_steps != 'ship_only',
                'usage': 'internal',
                'barcode': self._valid_barcode(code + '-OUTPUT', company_id),
                'warehouse_id': self.id
            },
            'wh_pack_stock_loc_id': {
                'name': _('Packing Zone'),
                'active': delivery_steps == 'pick_pack_ship',
                'usage': 'internal',
                'barcode': self._valid_barcode(code + '-PACKING', company_id),
                'warehouse_id': self.id
            },
        }
        return sub_locations
    