from odoo import models, fields, api
from datetime import timedelta
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone

class DailyReportInventory(models.TransientModel):
    _name="daily.report.inventory"
    _description='Daily Report Inventory'

    location_id = fields.Many2one('stock.location', string="Plant", required=True)
    product_ids = fields.Many2many('product.product', string="Sperpat", required=True)		
    from_date = fields.Date('From Date', default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
                            required=True)
    to_date = fields.Date("To Date", default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()), required=True)
    
    
    def print_report(self):
        datas = []
        locations = self.env["stock.location"].search([("id", "child_of", [self.location_id.id])])
        self._cr.execute(
            """
            SELECT move.date, move.product_id, move.product_qty,
                move.product_uom_qty, move.product_uom, move.reference,
                move.location_id, move.location_dest_id,
                case when move.location_dest_id in %s
                    then move.product_qty end as product_in,
                case when move.location_id in %s
                    then move.product_qty end as product_out,
                case when move.date < %s then True else False end as is_initial
            FROM stock_move move
            WHERE (move.location_id in %s or move.location_dest_id in %s)
                and move.state = 'done' and move.product_id in %s
                and CAST(move.date AS date) < %s
            ORDER BY move.date, move.reference
            """,
            (
                tuple(locations.ids),
                tuple(locations.ids),
                self.from_date,
                tuple(locations.ids),
                tuple(locations.ids),
                tuple(self.product_ids.ids),
                self.from_date,
            ),
            )
        stock_last_results = self._cr.dictfetchall()

        if self.product_ids and self.location_id:
            self._cr.execute(
            """
            SELECT move.date, move.product_id, move.product_qty,
                move.product_uom_qty, move.product_uom, move.reference,
                move.location_id, move.location_dest_id,
                case when move.location_dest_id in %s
                    then move.product_qty end as product_in,
                case when move.location_id in %s
                    then move.product_qty end as product_out,
                case when move.date < %s then True else False end as is_initial
            FROM stock_move move
            WHERE (move.location_id in %s or move.location_dest_id in %s)
                and move.state = 'done' and move.product_id in %s
                and CAST(move.date AS date) <= %s
            ORDER BY move.date, move.reference
            """,
            (
                tuple(locations.ids),
                tuple(locations.ids),
                self.from_date,
                tuple(locations.ids),
                tuple(locations.ids),
                tuple(self.product_ids.ids),
                self.to_date,
            ),
            )
            stock_card_results = self._cr.dictfetchall()
            for rec in self.product_ids:
                stock = [line for line in stock_card_results if line['product_id'] == rec.id]
                stock_last = [line for line in stock_last_results if line['product_id'] == rec.id]
                current_stock = sum(line.get('product_in', 0) or 0 for line in stock_last) - sum(line.get('product_out', 0) or 0 for line in stock_last)
            
                datas.append({
                    'id': rec.id,
                    'code_product': rec.default_code,
                    'product_id': rec.name,
                    'product_uom': rec.uom_id.name,
                    'stock_inventory': current_stock,
                    'stock_in': sum(line.get('product_in', 0) or 0 for line in stock),
                    'stock_out': sum(line.get('product_out', 0) or 0 for line in stock),
                    'stock_remaining': ((current_stock + sum(line.get('product_in', 0) or 0 for line in stock)) - sum(line.get('product_out', 0) or 0 for line in stock)),
                })
    


        res = {
            'stock':datas,
            'location': self.location_id.name,
            'start_date': str(self.from_date.strftime('%d-%m-%Y')),
            'end_date': str(self.to_date.strftime('%d-%m-%Y')),
            'date': str(self.from_date.strftime('%B %Y')),
        }
        data = {
            'form': res,
        }
        return self.env.ref('daily_report_inventory.stock_daily_request_report').report_action([],data=data)