# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta, datetime

class BaseImportImport(models.TransientModel):
    _inherit = 'base_import.import'

    @api.model
    def _prepare_create_values(self, values_list):
        print("Custom _prepare_create_values called")
        print(values_list)
        return super()._prepare_create_values(values_list)

    def _convert_import_data(self,fields,options):
        print("Custom _convert_import_data called")
        result = super()._convert_import_data(fields, options)
        print(result)
        return result