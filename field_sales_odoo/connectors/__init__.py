# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _

from field_sales_odoo.connectors.base import BaseConnector, ConnectorError
from field_sales_odoo.connectors.odoo import OdooConnector

CONNECTORS: dict[str, type[BaseConnector]] = {
	"Odoo": OdooConnector,
}

__all__ = ["BaseConnector", "ConnectorError", "CONNECTORS", "get_connector"]


def get_connector(require_enabled: bool = True) -> OdooConnector:
	settings = frappe.get_single("Store Connection")
	if require_enabled and not settings.enabled:
		frappe.throw(_("Store Connection is disabled"))

	connector_cls = CONNECTORS.get(settings.platform)
	if not connector_cls:
		frappe.throw(_("Platform {0} is not supported").format(settings.platform or _("(not set)")))

	return connector_cls(settings)
