# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


class ReportePersonalizadoXlsx(models.AbstractModel):
    _name = 'report.solt_library.report_loan_xlsx_template' # Debe coincidir con report_name en XML
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, loans):
        # Crear una hoja de cálculo
        sheet = workbook.add_worksheet('Préstamos de Libros')

        # Definir formatos
        bold_format = workbook.add_format({'bold': True})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})

        # Escribir encabezados
        headers = ['ID del Préstamo', 'Título del Libro', 'Usuario', 'Autores', 'Fecha de Préstamo', 'Fecha de Devolución']
        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header, bold_format)

        # Escribir datos de préstamos
        for row_num, loan in enumerate(loans, start=1):
            sheet.write(row_num, 0, loan.id)
            sheet.write(row_num, 1, loan.book_id.name or '',bold_format)
            sheet.write(row_num, 2, loan.user_id.name or '')
            sheet.write(row_num, 3, ', '.join(author.name for author in loan.book_id.author_ids) if loan.book_id.author_ids else '')
            # Escribir fechas como texto si son nulas
            sheet.write(row_num, 4, loan.loan_date.strftime('%Y-%m-%d') if loan.loan_date else '', date_format)
            sheet.write(row_num, 5, loan.expected_return_date.strftime('%Y-%m-%d') if loan.expected_return_date else '', date_format)
