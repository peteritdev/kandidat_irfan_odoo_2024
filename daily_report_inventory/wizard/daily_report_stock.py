from odoo import models, fields, api
from datetime import timedelta
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone

class DailyReportInventory(models.TransientModel):
    _name="daily.report.inventory"
    _description='Daily Report Inventory'

    warehouse_id = fields.Many2one('stock.warehouse', string="Plant")
    product_id = fields.Many2one('product.product', string="SKU")		
    from_date = fields.Date('From Date', default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
                            required=True)
    to_date = fields.Date("To Date", default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()), required=True)
    
    
    def print_report(self):
        datas = []

        if self.warehouse_id and not self.product_id:
            warehouse = self.env['stock.move'].search(
                        [('location_dest_id.warehouse_id', '=', self.warehouse_id.id), ('state', '=', 'done')]).product_id

            for produk in warehouse:
                stock_inventory_current = self.env['stock.move'].search(
                            [('product_id', '=', produk.id), ('location_dest_id.warehouse_id', '=', self.warehouse_id.id), ('date', '<', self.from_date),
                             ('location_id.usage', '=', 'inventory'), ('state', '=', 'done')])
                stock_in_current  = self.env['stock.move'].search(
                            [('product_id', '=', produk.id), ('location_dest_id.warehouse_id', '=', self.warehouse_id.id), ('date', '<', self.from_date), 
                             ('location_dest_id.name', '=', 'Stock'), ('picking_type_id.code', '=', ('incoming', 'mrp_operation')), ('state', '=', 'done')])
                stock_out_current  = self.env['stock.move'].search(
                            [('product_id', '=', produk.id), ('location_id.warehouse_id', '=', self.warehouse_id.id), ('date', '<', self.from_date), 
                             ('location_dest_id.name', '!=', 'Stock'), ('state', '=', 'done')])
                
                current_stock = ((sum(stock_inventory_current.mapped('product_uom_qty')) + sum(stock_in_current.mapped('product_uom_qty'))) - sum(stock_out_current.mapped('product_uom_qty')))

                stock_inventory = self.env['stock.move'].search(
                            [('product_id', '=', produk.id), ('location_dest_id.warehouse_id', '=', self.warehouse_id.id), ('date', '>=', self.from_date), 
                             ('date', '<=', self.to_date), ('location_id.usage', '=', 'inventory'), ('state', '=', 'done')])
                stock_in = self.env['stock.move'].search(
                            [('product_id', '=', produk.id), ('location_dest_id.warehouse_id', '=', self.warehouse_id.id), ('date', '>=', self.from_date), 
                             ('date', '<=', self.to_date), ('location_dest_id.name', '=', 'Stock'), ('picking_type_id.code', '=', ('incoming', 'mrp_operation')), ('state', '=', 'done')])
                stock_out = self.env['stock.move'].search(
                            [('product_id', '=', produk.id), ('location_id.warehouse_id', '=', self.warehouse_id.id), ('date', '>=', self.from_date), 
                             ('date', '<=', self.to_date), ('location_dest_id.name', '!=', 'Stock'), ('state', '=', 'done')])
            
                datas.append({
                            'id': produk.id,
                            'code_product': produk.default_code,
                            'product_id': produk.name,
                            'product_uom': produk.uom_id.name,
                            'stock_inventory': current_stock,
                            'stock_in': sum(stock_in.mapped('product_uom_qty')),
                            'stock_out': sum(stock_out.mapped('product_uom_qty')),
                            'stock_remaining': ((current_stock + sum(stock_in.mapped('product_uom_qty'))) - sum(stock_out.mapped('product_uom_qty'))),
                })
        
        if self.product_id and not self.warehouse_id:
            warehouse_name = self.env['stock.move'].search([('product_id', '=', self.product_id.id),('state', '=', 'done')]).location_dest_id.warehouse_id
            for rek in warehouse_name:
                warehouse_data = {
                                'name': rek.name,
                                'warehouse': []
                                }
                warehouse = self.env['stock.move'].search([('product_id', '=', self.product_id.id), ('location_dest_id.warehouse_id', '=', rek.id), ('state', '=', 'done')])
                for produk in warehouse:
                    stock_inventory_current = self.env['stock.move'].search(
                                [('product_id', '=', produk.product_id.id), ('location_dest_id.warehouse_id', '=', rek.id), ('date', '<', self.from_date),
                                 ('location_id.usage', '=', 'inventory'), ('state', '=', 'done')])
                    stock_in_current = self.env['stock.move'].search(
                            [('product_id', '=', produk.product_id.id), ('location_dest_id.warehouse_id', '=', rek.id), ('date', '<', self.from_date), 
                             ('location_dest_id.name', '=', 'Stock'), ('picking_type_id.code', '=', ('incoming', 'mrp_operation')), ('state', '=', 'done')])
                    stock_out_current = self.env['stock.move'].search(
                            [('product_id', '=', produk.product_id.id), ('location_id.warehouse_id', '=', rek.id), ('date', '<', self.from_date), 
                             ('location_dest_id.name', '!=', 'Stock'), ('state', '=', 'done')])
                    
                    current_stock = ((sum(stock_inventory_current.mapped('product_uom_qty')) + sum(stock_in_current.mapped('product_uom_qty'))) - sum(stock_out_current.mapped('product_uom_qty')))

                    stock_inventory = self.env['stock.move'].search(
                                [('product_id', '=', produk.product_id.id), ('location_dest_id.warehouse_id', '=', rek.id), ('date', '>=', self.from_date),
                                ('date', '<=', self.to_date), ('location_id.usage', '=', 'inventory'), ('state', '=', 'done')])
                    stock_in = self.env['stock.move'].search(
                            [('product_id', '=', produk.product_id.id), ('location_dest_id.warehouse_id', '=', rek.id), ('date', '>=', self.from_date), 
                            ('date', '<=', self.to_date), ('location_dest_id.name', '=', 'Stock'), ('picking_type_id.code', '=', ('incoming', 'mrp_operation')), ('state', '=', 'done')])
                    stock_out = self.env['stock.move'].search(
                            [('product_id', '=', produk.product_id.id), ('location_id.warehouse_id', '=', rek.id), ('date', '>=', self.from_date), 
                            ('date', '<=', self.to_date), ('location_dest_id.name', '!=', 'Stock'), ('state', '=', 'done')])
            
                    warehouse_data['warehouse'].append({
                                'id': produk.product_id.id,
                                'code_product': produk.product_id.default_code,
                                'product_id': produk.product_id.name,
                                'product_uom': produk.product_id.uom_id.name,
                                'stock_inventory': current_stock,
                                'stock_in': sum(stock_in.mapped('product_uom_qty')),
                                'stock_out': sum(stock_out.mapped('product_uom_qty')),
                                'stock_remaining': ((current_stock + sum(stock_in.mapped('product_uom_qty'))) - sum(stock_out.mapped('product_uom_qty'))),
                    })
                datas.append(warehouse_data)
        
        if self.product_id and self.warehouse_id:
            stock_inventory_current = self.env['stock.move'].search(
                            [('product_id', '=', self.product_id.id), ('location_dest_id.warehouse_id', '=', self.warehouse_id.id), ('date', '<', self.from_date),
                             ('location_id.usage', '=', 'inventory'), ('state', '=', 'done')])
            stock_in_current = self.env['stock.move'].search(
                            [('product_id', '=', self.product_id.id), ('location_dest_id.warehouse_id', '=', self.warehouse_id.id), ('date', '<', self.from_date), 
                             ('location_dest_id.name', '=', 'Stock'), ('picking_type_id.code', '=', ('incoming', 'mrp_operation')), ('state', '=', 'done')])
            stock_out_current = self.env['stock.move'].search(
                            [('product_id', '=', self.product_id.id), ('location_id.warehouse_id', '=', self.warehouse_id.id), ('date', '<', self.from_date), 
                             ('location_dest_id.name', '!=', 'Stock'), ('state', '=', 'done')])

            current_stock = ((sum(stock_inventory_current.mapped('product_uom_qty')) + sum(stock_in_current.mapped('product_uom_qty'))) - sum(stock_out_current.mapped('product_uom_qty')))

            stock_inventory = self.env['stock.move'].search(
                            [('product_id', '=', self.product_id.id), ('location_dest_id.warehouse_id', '=', self.warehouse_id.id), ('date', '>=', self.from_date),
                             ('date', '<=', self.to_date), ('location_id.usage', '=', 'inventory'), ('state', '=', 'done')])
            stock_in = self.env['stock.move'].search(
                            [('product_id', '=', self.product_id.id), ('location_dest_id.warehouse_id', '=', self.warehouse_id.id), ('date', '>=', self.from_date), 
                             ('date', '<=', self.to_date), ('location_dest_id.name', '=', 'Stock'), ('picking_type_id.code', '=', ('incoming', 'mrp_operation')), ('state', '=', 'done')])
            stock_out = self.env['stock.move'].search(
                            [('product_id', '=', self.product_id.id), ('location_id.warehouse_id', '=', self.warehouse_id.id), ('date', '>=', self.from_date), 
                             ('date', '<=', self.to_date), ('location_dest_id.name', '!=', 'Stock'), ('state', '=', 'done')])
            
            datas.append({
                          'id': self.product_id.id,
                          'code_product': self.product_id.default_code,
                          'product_id': self.product_id.name,
                          'product_uom': self.product_id.uom_id.name,
                          'stock_inventory': current_stock,
                          'stock_in': sum(stock_in.mapped('product_uom_qty')),
                          'stock_out': sum(stock_out.mapped('product_uom_qty')),
                          'stock_remaining': ((current_stock + sum(stock_in.mapped('product_uom_qty'))) - sum(stock_out.mapped('product_uom_qty'))),
                })
        

        if not self.warehouse_id and not self.product_id:
            warehouse_name = self.env['stock.move'].search([('state', '=', 'done')]).location_dest_id.warehouse_id
            for rek in warehouse_name:
                warehouse_data = {
                                'name': rek.name,
                                'warehouse': []
                                }
                warehouse = self.env['stock.move'].search([('location_dest_id.warehouse_id', '=', rek.id), ('state', '=', 'done')]).product_id 
                for produk in warehouse:
                    stock_inventory_current = self.env['stock.move'].search(
                            [('product_id', '=', produk.id), ('location_dest_id.warehouse_id', '=', rek.id), ('date', '<', self.from_date), 
                             ('location_id.usage', '=', 'inventory'), ('state', '=', 'done')])
                    stock_in_current = self.env['stock.move'].search(
                            [('product_id', '=', produk.id), ('location_dest_id.warehouse_id', '=', rek.id), ('date', '<', self.from_date), 
                             ('location_dest_id.name', '=', 'Stock'), ('picking_type_id.code', '=', ('incoming', 'mrp_operation')), ('state', '=', 'done')])
                    stock_out_current = self.env['stock.move'].search(
                            [('product_id', '=', produk.id), ('location_id.warehouse_id', '=', rek.id), ('date', '<', self.from_date), 
                             ('location_dest_id.name', '!=', 'Stock'), ('state', '=', 'done')])
                    
                    current_stock = ((sum(stock_inventory_current.mapped('product_uom_qty')) + sum(stock_in_current.mapped('product_uom_qty'))) - sum(stock_out_current.mapped('product_uom_qty')))
                    
                    stock_inventory = self.env['stock.move'].search(
                            [('product_id', '=', produk.id), ('location_dest_id.warehouse_id', '=', rek.id), ('date', '>=', self.from_date), ('date', '<=', self.to_date), 
                             ('location_id.usage', '=', 'inventory'), ('state', '=', 'done')])
                    stock_in = self.env['stock.move'].search(
                            [('product_id', '=', produk.id), ('location_dest_id.warehouse_id', '=', rek.id), ('date', '>=', self.from_date), ('date', '<=', self.to_date), 
                             ('location_dest_id.name', '=', 'Stock'), ('picking_type_id.code', '=', ('incoming', 'mrp_operation')), ('state', '=', 'done')])
                    stock_out = self.env['stock.move'].search(
                            [('product_id', '=', produk.id), ('location_id.warehouse_id', '=', rek.id), ('date', '>=', self.from_date), ('date', '<=', self.to_date), 
                             ('location_dest_id.name', '!=', 'Stock'), ('state', '=', 'done')]) 
                    warehouse_data['warehouse'].append({
                                'id': produk.id,
                                'code_product': produk.default_code,
                                'product_id': produk.name,
                                'product_uom': produk.uom_id.name,
                                'stock_inventory': current_stock,
                                'stock_in': sum(stock_in.mapped('product_uom_qty')),
                                'stock_out': sum(stock_out.mapped('product_uom_qty')),
                                'stock_remaining': ((sum(stock_inventory.mapped('product_uom_qty'))+sum(stock_in.mapped('product_uom_qty')))-sum(stock_out.mapped('product_uom_qty'))),
                    })
                datas.append(warehouse_data)


        res = {
            'stock':datas,
            'warehouse': self.warehouse_id.name,
            'product': self.product_id.name,
            'start_date': str(self.from_date.strftime('%d-%m-%Y')),
            'end_date': str(self.to_date.strftime('%d-%m-%Y')),
            'date': str(self.from_date.strftime('%B %Y')),
        }
        data = {
            'form': res,
        }
        return self.env.ref('daily_report_inventory.stock_daily_request_report').report_action([],data=data)