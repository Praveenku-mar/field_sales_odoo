# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

"""
What Shopify and WooCommerce tell us by webhook, Odoo is asked for (it cannot sign webhooks,
so connectors/odoo.py refuses them). Every 15 minutes:

- Orders: of the Field Orders pushed to Odoo in the last ORDER_DAYS days, the ones whose sale
  order, invoice or payment changed since the last check go through ``reconcile_order`` — the
  path an order webhook takes on the other platforms — so paid / delivered / cancelled /
  refunded reach commission — and ``apply_store_payment``, so an order paid on Odoo (invoice
  or portal payment) is paid in Agamsale too.
- Products: products, variants and stock that changed since the last check go through
  ``sync_one_product`` — the product webhook's path — so prices, archiving and stock follow.

Each check remembers when it ran (site defaults, so a Redis restart does not reset it) and asks
from a few minutes before that, to cover clock skew and changes made during the run. A store
error keeps the old mark, so the next run asks again.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import frappe
from frappe.utils import add_days, cint, nowdate

from field_sales_odoo.commission import commission_enabled
from field_sales_odoo.commission.engine import reconcile_order
from field_sales_odoo.connectors import ConnectorError, get_connector
from field_sales_odoo.field_sales_odoo.doctype.sync_log.sync_log import log_sync, log_sync_durable
from field_sales_odoo.payments.store_payments import apply_store_payment
from field_sales_odoo.sync.products import sync_one_product
from field_sales_odoo.utils.db import safe_commit

ORDERS_MARK = "field_sales_odoo_orders_checked_until"
PRODUCTS_MARK = "field_sales_odoo_products_checked_until"
OVERLAP = timedelta(minutes=5)
FIRST_LOOKBACK = timedelta(days=1)
ORDER_DAYS = 180  # older orders' commission is settled; a refund that late is rare
MAX_PER_RUN = 500
ODOO_TIME = "%Y-%m-%d %H:%M:%S"  # Odoo keeps write_date in UTC, without a zone


def poll_store_changes():
	"""Scheduler (every 15 minutes): bring Odoo's order and product changes in."""
	settings = frappe.get_single("Store Connection")
	if not cint(settings.enabled) or settings.platform != "Odoo":
		return
	try:
		conn = get_connector()
	except frappe.ValidationError:
		return  # not configured yet
	_run(ORDERS_MARK, "Commission", lambda since: _changed_orders(conn, since), lambda oid: _apply_order(conn, oid))
	if settings.default_location_id:
		_run(PRODUCTS_MARK, "Product Sync", lambda since: conn.get_changed_product_ids(since), lambda pid: sync_one_product(conn, pid))


def _run(mark: str, operation: str, fetch, apply) -> dict:
	started = datetime.now(timezone.utc)
	since = _since(mark, started)
	try:
		ids = sorted(fetch(since.strftime(ODOO_TIME)))
	except ConnectorError as e:
		log_sync_durable(
			platform="Odoo",
			operation=operation,
			status="Failed",
			error_code=e.code or "ConnectorError",
			error_message=f"Checking Odoo for changes failed: {e.message}",
		)
		return {"error": e.message}

	done = failed = 0
	for external_id in ids[:MAX_PER_RUN]:
		try:
			apply(external_id)
			safe_commit()
			done += 1
		except Exception:
			frappe.db.rollback()
			failed += 1
			frappe.log_error(title=f"Odoo change polling failed: {operation} {external_id}")
	# Over the cap, the rest wait for the next full product sync / a later change.
	frappe.db.set_default(mark, started.strftime(ODOO_TIME))
	safe_commit()
	if ids:
		log_sync(
			platform="Odoo",
			operation=operation,
			status="Failed" if failed and not done else "Success",
			response_payload=frappe.as_json(
				{"changed": len(ids), "applied": done, "failed": failed, "skipped": max(0, len(ids) - MAX_PER_RUN)}
			),
		)
		safe_commit()
	return {"changed": len(ids), "applied": done, "failed": failed}


def _since(mark: str, now: datetime) -> datetime:
	stored = frappe.db.get_default(mark)
	try:
		last = datetime.strptime(stored, ODOO_TIME).replace(tzinfo=timezone.utc) if stored else None
	except ValueError:
		last = None
	return (last or now - FIRST_LOOKBACK) - OVERLAP


def _changed_orders(conn, since: str) -> set[str]:
	ids = frappe.get_all(
		"Field Order",
		filters={
			"docstatus": ("in", (1, 2)),
			"external_order_id": ("is", "set"),
			"order_date": (">=", add_days(nowdate(), -ORDER_DAYS)),
		},
		pluck="external_order_id",
	)
	return conn.get_changed_order_ids(ids, since) if ids else set()


def _apply_order(conn, external_order_id: str):
	"""What an order webhook does elsewhere: commission (when on) and a payment made on Odoo."""
	if commission_enabled():
		reconcile_order(external_order_id)
	apply_store_payment(conn, external_order_id)
