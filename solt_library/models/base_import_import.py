# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta, datetime
import logging
_logger = logging.getLogger(__name__)

class BaseImportImport(models.TransientModel):
    _inherit = 'base_import.import'

    @api.model
    def _prepare_create_values(self, values_list):
        _logger.info("Custom _prepare_create_values called with values_list: %s", values_list)
        _logger.info("Number of records to create: %d", len(values_list))
        return super()._prepare_create_values(values_list)

    def _convert_import_data(self,fields,options):
        _logger.info("Custom _convert_import_data called with fields: %s and options: %s", fields, options)
        _logger.info("Number of fields: %d", len(fields))
        result = super()._convert_import_data(fields, options)
        _logger.info("Converted data: %s", result)
        return result