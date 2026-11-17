# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

"""
A payment made on the store marks the Field Order paid (payments/store_payments.py). The same
file runs in every Field Sales edition; each platform's own rule for "paid" is tested with its
connector.
"""

import importlib
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

APP = __name__.split(".", 1)[0]
store_payments = importlib.import_module(f"{APP}.payments.store_payments")
links = importlib.import_module(f"{APP}.tests.test_razorpay_links")


class TestStorePayments(links.LinkFixture, IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_value("Field Order", self.order.name, "external_order_id", "7001")
		self.total = frappe.db.get_value("Field Order", self.order.name, "grand_total")
		self.conn = MagicMock()
		notify = patch.object(store_payments, "notify_payment_received")
		self.notify = notify.start()
		self.addCleanup(notify.stop)

	def saved(self, *fields):
		return frappe.db.get_value("Field Order", self.order.name, list(fields), as_dict=True)

	def paid(self, amount, **extra):
		return {"amount": amount, "currency": "INR", "method": "Card", "reference": "txn_1", "paid_at": "2026-11-16T04:30:00Z", **extra}

	def history(self):
		return frappe.get_all(
			"Payment Transaction",
			filters={"reference_order": self.order.name, "transaction_key": "store:7001"},
			fields=["status", "amount", "source", "method", "reference"],
		)

	def test_paid_in_full_on_the_store(self):
		self.conn.get_store_payment.return_value = self.paid(self.total)
		result = store_payments.apply_store_payment(self.conn, "7001")
		self.assertEqual(result["payment_status"], "Paid")
		o = self.saved("payment_status", "amount_paid", "store_marked_paid_on", "paid_on")
		self.assertEqual((o.payment_status, o.amount_paid), ("Paid", self.total))
		self.assertIsNotNone(o.store_marked_paid_on)
		self.assertIsNotNone(o.paid_on)
		(row,) = self.history()
		self.assertEqual((row.status, row.source, row.method, row.reference), ("Captured", "Store Checkout", "Card", "txn_1"))
		self.notify.assert_called_once()

	def test_part_then_rest_updates_one_history_row(self):
		self.conn.get_store_payment.return_value = self.paid(100)
		store_payments.apply_store_payment(self.conn, "7001")
		self.assertEqual(self.saved("payment_status").payment_status, "Partially Paid")
		self.conn.get_store_payment.return_value = self.paid(self.total)
		store_payments.apply_store_payment(self.conn, "7001")
		self.assertEqual(self.saved("payment_status").payment_status, "Paid")
		(row,) = self.history()
		self.assertEqual(row.amount, self.total)

	def test_repeat_changes_nothing(self):
		self.conn.get_store_payment.return_value = self.paid(100)
		store_payments.apply_store_payment(self.conn, "7001")
		self.assertIn("Ignored", store_payments.apply_store_payment(self.conn, "7001")["note"])
		self.notify.assert_called_once()

	def test_more_than_the_order_is_capped(self):
		self.conn.get_store_payment.return_value = self.paid(self.total + 500)
		store_payments.apply_store_payment(self.conn, "7001")
		self.assertEqual(self.saved("amount_paid").amount_paid, self.total)

	def test_already_paid_in_agamsale_is_left_alone(self):
		frappe.db.set_value(
			"Field Order",
			self.order.name,
			{"payment_status": "Paid", "amount_paid": self.total, "store_marked_paid_on": "2026-11-16 10:00:00"},
		)
		self.assertIn("Ignored", store_payments.apply_store_payment(self.conn, "7001")["note"])
		self.conn.get_store_payment.assert_not_called()

	def test_paid_in_agamsale_then_on_the_store_is_noted_once(self):
		frappe.db.set_value("Field Order", self.order.name, {"payment_status": "Paid", "amount_paid": self.total})
		self.conn.get_store_payment.return_value = None
		self.assertIn("not paid on the store yet", store_payments.apply_store_payment(self.conn, "7001")["note"])
		self.assertIsNone(self.saved("store_marked_paid_on").store_marked_paid_on)

		# The merchant records the cash payment on the store.
		self.conn.get_store_payment.return_value = self.paid(self.total, method="Cash on Delivery (COD)")
		self.assertEqual(store_payments.apply_store_payment(self.conn, "7001")["note"], "Paid on the store too")
		o = self.saved("store_marked_paid_on", "amount_paid", "payment_status")
		self.assertIsNotNone(o.store_marked_paid_on)
		self.assertEqual((o.payment_status, o.amount_paid), ("Paid", self.total))
		self.assertEqual(self.history(), [])  # no second payment
		self.notify.assert_not_called()

		self.conn.get_store_payment.reset_mock()
		self.assertIn("Ignored", store_payments.apply_store_payment(self.conn, "7001")["note"])
		self.conn.get_store_payment.assert_not_called()

	def test_unpaid_or_unknown_store_order(self):
		self.conn.get_store_payment.return_value = None
		self.assertIn("Ignored", store_payments.apply_store_payment(self.conn, "7001")["note"])
		self.assertEqual(self.saved("payment_status").payment_status, "Unpaid")
		self.assertIn("Ignored", store_payments.apply_store_payment(self.conn, "999999")["note"])

	def test_open_payment_link_is_cancelled(self):
		frappe.db.set_value("Field Order", self.order.name, {"payment_status": "Link Sent", "razorpay_payment_link_id": "plink_9"})
		self.conn.get_store_payment.return_value = self.paid(self.total)
		with patch.object(store_payments, "fetch_payment_link", return_value={"status": "created", "amount_paid": 0}), patch.object(
			store_payments, "cancel_payment_link"
		) as cancel:
			store_payments.apply_store_payment(self.conn, "7001")
		cancel.assert_called_once()
		self.assertEqual(self.saved("payment_status").payment_status, "Paid")

	def test_paid_link_wins(self):
		frappe.db.set_value("Field Order", self.order.name, {"payment_status": "Link Sent", "razorpay_payment_link_id": "plink_9"})
		self.conn.get_store_payment.return_value = self.paid(self.total)
		with patch.object(store_payments, "fetch_payment_link", return_value={"status": "paid", "amount_paid": 100}):
			result = store_payments.apply_store_payment(self.conn, "7001")
		self.assertIn("payment link", result["note"])
		self.assertEqual(self.saved("payment_status").payment_status, "Link Sent")

	def test_store_time_in_utc_becomes_system_time(self):
		naive = store_payments._when("2026-11-16 04:30:00")
		zulu = store_payments._when("2026-11-16T04:30:00Z")
		self.assertEqual(naive, zulu)
		self.assertIsNone(zulu.tzinfo)


class TestOdooPaidRule(IntegrationTestCase):
	"""Odoo: paid on posted invoices (credit notes off), else done transactions; the portal link."""

	def conn(self, order, moves=(), transactions=()):
		from field_sales_odoo.tests.test_odoo_connector import make_connector

		conn = make_connector()
		conn._read = MagicMock(side_effect=lambda model, ids, fields, op, ref=None: [order] if model == "sale.order" else list(moves))
		conn._search_read = MagicMock(return_value=list(transactions))
		return conn

	def test_invoices(self):
		order = {"state": "sale", "currency_id": [1, "INR"], "invoice_ids": [5, 6]}
		moves = [
			{"state": "posted", "move_type": "out_invoice", "payment_state": "paid", "amount_total": 1180, "amount_residual": 0, "name": "INV/1", "write_date": "2026-11-16 04:30:00"},
			{"state": "posted", "move_type": "out_refund", "payment_state": "paid", "amount_total": 180, "amount_residual": 0, "name": "RINV/1", "write_date": "2026-11-16 05:00:00"},
		]
		payment = self.conn(order, moves).get_store_payment("12")
		self.assertEqual((payment["amount"], payment["currency"], payment["reference"]), (1000, "INR", "INV/1"))

	def test_draft_or_unpaid_invoice_and_cancelled_order(self):
		order = {"state": "sale", "currency_id": [1, "INR"], "invoice_ids": [5]}
		unpaid = [{"state": "posted", "move_type": "out_invoice", "payment_state": "not_paid", "amount_total": 1180, "amount_residual": 1180}]
		self.assertIsNone(self.conn(order, unpaid).get_store_payment("12"))
		self.assertIsNone(self.conn({**order, "state": "cancel"}, unpaid).get_store_payment("12"))

	def test_done_transaction_without_invoice(self):
		order = {"state": "sale", "currency_id": [1, "INR"], "invoice_ids": []}
		payment = self.conn(order, transactions=[{"amount": 1180, "reference": "S00012-1", "last_state_change": "2026-11-16 04:30:00"}]).get_store_payment("12")
		self.assertEqual((payment["amount"], payment["method"], payment["reference"]), (1180, "Online payment", "S00012-1"))

	def test_portal_link(self):
		from field_sales_odoo.connectors.base import ConnectorError
		from field_sales_odoo.tests.test_odoo_connector import make_connector

		conn = make_connector()
		with patch.object(conn, "_execute_kw", return_value="/my/orders/12?access_token=abc"):
			self.assertEqual(conn._portal_url(12), "https://store.example/my/orders/12?access_token=abc")
		with patch.object(conn, "_execute_kw", side_effect=ConnectorError("no access", code="HTTP_ERROR")):
			self.assertIsNone(conn._portal_url(12))
		conn.base_url = "http://store.example"
		with patch.object(conn, "_execute_kw", return_value="/my/orders/12?access_token=abc"):
			self.assertIsNone(conn._portal_url(12))
