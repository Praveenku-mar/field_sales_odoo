# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

"""Odoo change polling (sync/polling.py and the connector's change queries). No network."""

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from field_sales_odoo.connectors.base import ConnectorError
from field_sales_odoo.sync import polling
from field_sales_odoo.tests.test_odoo_connector import make_connector

# The real function, before the tests below patch it out.
REAL_CHANGED_ORDERS = polling._changed_orders


class TestChangeQueries(IntegrationTestCase):
	def test_changed_orders_ask_for_order_invoice_and_payment_changes(self):
		conn = make_connector()
		calls = []

		def fake(model, domain, fields, operation, **kwargs):
			calls.append((model, domain))
			return [{"id": 7001}]

		with patch.object(conn, "_search_read", side_effect=fake):
			changed = conn.get_changed_order_ids(["7001", "7002", "not-an-id"], "2026-11-16 10:00:00")
		self.assertEqual(changed, {"7001"})
		model, domain = calls[0]
		self.assertEqual(model, "sale.order")
		self.assertEqual(domain[0], ("id", "in", [7001, 7002]))
		self.assertEqual(domain[1:3], ["|", "|"])
		fields = {clause[0] for clause in domain[3:]}
		self.assertEqual(fields, {"write_date", "transaction_ids.write_date", "order_line.invoice_lines.move_id.write_date"})

	def test_older_odoo_without_a_field_falls_back(self):
		conn = make_connector()
		domains = []

		def fake(model, domain, fields, operation, **kwargs):
			domains.append(domain)
			if len(domains) < 3:
				raise ConnectorError("Invalid field", code="BAD_FIELD")
			return []

		with patch.object(conn, "_search_read", side_effect=fake):
			self.assertEqual(conn.get_changed_order_ids(["5"], "2026-11-16 10:00:00"), set())
		# Transactions dropped first, then invoices; the order's own changes are always asked.
		self.assertEqual(domains[-1], [("id", "in", [5]), ("write_date", ">", "2026-11-16 10:00:00")])

	def test_other_errors_are_not_swallowed(self):
		conn = make_connector()
		with patch.object(conn, "_search_read", side_effect=ConnectorError("down", code="NETWORK_ERROR")):
			self.assertRaises(ConnectorError, conn.get_changed_order_ids, ["5"], "2026-11-16 10:00:00")

	def test_changed_products_include_variants_and_stock(self):
		conn = make_connector()

		def fake(model, domain, fields, operation, **kwargs):
			return {
				"product.template": [{"id": 10}],
				"product.product": [{"product_tmpl_id": [11, "Variant"]}],
				"stock.quant": [{"product_id": [300, "Widget"]}],
			}[model]

		with patch.object(conn, "_search_read", side_effect=fake), patch.object(
			conn, "_read", return_value=[{"product_tmpl_id": [12, "Widget"]}]
		) as read:
			self.assertEqual(conn.get_changed_product_ids("2026-11-16 10:00:00"), {"10", "11", "12"})
		read.assert_called_once_with("product.product", [300], ["product_tmpl_id"], "Stock Check")

	def test_store_without_inventory_still_reports_product_changes(self):
		conn = make_connector()

		def fake(model, domain, fields, operation, **kwargs):
			if model == "stock.quant":
				raise ConnectorError("Object stock.quant doesn't exist", code="NOT_FOUND")
			return [{"id": 10}] if model == "product.template" else []

		with patch.object(conn, "_search_read", side_effect=fake):
			self.assertEqual(conn.get_changed_product_ids("2026-11-16 10:00:00"), {"10"})


class TestPollStoreChanges(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value(
			"Store Connection", {"enabled": 1, "platform": "Odoo", "default_location_id": "1"}
		)
		frappe.db.set_default(polling.ORDERS_MARK, "")
		frappe.db.set_default(polling.PRODUCTS_MARK, "")
		self.conn = MagicMock()
		self.conn.get_changed_order_ids.return_value = {"7001", "7002"}
		self.conn.get_changed_product_ids.return_value = {"10"}
		for target, value in [
			("get_connector", self.conn),
			("commission_enabled", True),
		]:
			p = patch.object(polling, target, return_value=value)
			p.start()
			self.addCleanup(p.stop)
		p = patch.object(polling, "apply_store_payment")
		self.store_payment = p.start()
		self.addCleanup(p.stop)
		p = patch.object(polling, "_changed_orders", side_effect=lambda conn, since: conn.get_changed_order_ids(["7001", "7002"], since))
		p.start()
		self.addCleanup(p.stop)

	def tearDown(self):
		frappe.db.rollback()

	def test_changed_orders_and_products_go_through_the_webhook_paths(self):
		with patch.object(polling, "reconcile_order") as reconcile, patch.object(polling, "sync_one_product") as sync_one:
			polling.poll_store_changes()
		self.assertEqual(sorted(c.args[0] for c in reconcile.call_args_list), ["7001", "7002"])
		sync_one.assert_called_once_with(self.conn, "10")
		self.assertTrue(frappe.db.get_default(polling.ORDERS_MARK))
		self.assertTrue(frappe.db.get_default(polling.PRODUCTS_MARK))

	def test_next_run_asks_from_the_last_mark_minus_the_overlap(self):
		frappe.db.set_default(polling.ORDERS_MARK, "2026-11-16 10:00:00")
		with patch.object(polling, "reconcile_order"), patch.object(polling, "sync_one_product"):
			polling.poll_store_changes()
		since = self.conn.get_changed_order_ids.call_args.args[1]
		self.assertEqual(since, "2026-11-16 09:55:00")

	def test_store_error_keeps_the_mark(self):
		frappe.db.set_default(polling.ORDERS_MARK, "2026-11-16 10:00:00")
		self.conn.get_changed_order_ids.side_effect = ConnectorError("down", code="NETWORK_ERROR")
		with patch.object(polling, "reconcile_order") as reconcile, patch.object(polling, "sync_one_product"):
			polling.poll_store_changes()
		reconcile.assert_not_called()
		self.assertEqual(frappe.db.get_default(polling.ORDERS_MARK), "2026-11-16 10:00:00")

	def test_one_failing_order_does_not_stop_the_others(self):
		def reconcile(external_id):
			if external_id == "7001":
				raise RuntimeError("boom")

		with patch.object(polling, "reconcile_order", side_effect=reconcile) as rec, patch.object(polling, "sync_one_product"), patch.object(
			polling.frappe, "log_error"
		):
			polling.poll_store_changes()
		self.assertEqual(rec.call_count, 2)

	def test_nothing_runs_for_a_disabled_or_other_store(self):
		frappe.db.set_single_value("Store Connection", "enabled", 0)
		with patch.object(polling, "reconcile_order") as reconcile:
			polling.poll_store_changes()
		reconcile.assert_not_called()
		self.conn.get_changed_order_ids.assert_not_called()

	def test_commission_off_still_follows_store_payments_and_products(self):
		with patch.object(polling, "commission_enabled", return_value=False), patch.object(
			polling, "reconcile_order"
		) as reconcile, patch.object(polling, "sync_one_product") as sync_one:
			polling.poll_store_changes()
		reconcile.assert_not_called()
		self.assertEqual(sorted(c.args[1] for c in self.store_payment.call_args_list), ["7001", "7002"])
		sync_one.assert_called_once()

	def test_order_window_and_status_filters(self):
		conn = MagicMock()
		conn.get_changed_order_ids.return_value = {"7001"}
		real_get_all = frappe.get_all
		seen = {}

		def field_orders(answer):
			# Only the Field Order query is answered here; Frappe's own reads go through.
			def get_all(doctype, *args, **kwargs):
				if doctype != "Field Order":
					return real_get_all(doctype, *args, **kwargs)
				seen.update(kwargs)
				return answer
			return get_all

		with patch.object(polling.frappe, "get_all", side_effect=field_orders(["7001"])):
			self.assertEqual(REAL_CHANGED_ORDERS(conn, "2026-11-16 10:00:00"), {"7001"})
		filters = seen["filters"]
		# Submitted and cancelled orders (a cancel / refund must still reverse commission).
		self.assertEqual(filters["docstatus"], ("in", (1, 2)))
		self.assertEqual(filters["external_order_id"], ("is", "set"))
		self.assertEqual(filters["order_date"][0], ">=")
		conn.get_changed_order_ids.assert_called_once_with(["7001"], "2026-11-16 10:00:00")

		conn.reset_mock()
		with patch.object(polling.frappe, "get_all", side_effect=field_orders([])):
			self.assertEqual(REAL_CHANGED_ORDERS(conn, "2026-11-16 10:00:00"), set())
		conn.get_changed_order_ids.assert_not_called()
