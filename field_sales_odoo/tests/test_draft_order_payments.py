# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

"""
A quotation confirmed in Odoo carries its payment across (sync/orders.py link_completed_drafts):
paid on Odoo (portal pay link, invoice) → the Field Order is paid; paid in Agamsale (cash, bank,
Razorpay) → the Odoo order is marked paid.
"""

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from field_sales_odoo.connectors import ConnectorError
from field_sales_odoo.sync import orders
from field_sales_odoo.tests import test_razorpay_links as links


class TestDraftOrderPayments(links.LinkFixture, IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("Store Connection", "enabled", 1)  # both jobs skip a disabled store
		self.total = frappe.db.get_value("Field Order", self.order.name, "grand_total")
		# Paid in Agamsale (cash), pushed as quotation 42, not confirmed in Odoo yet.
		frappe.db.set_value(
			"Field Order",
			self.order.name,
			{
				"payment_status": "Paid",
				"amount_paid": self.total,
				"paid_on": now_datetime(),
				"manual_payment_method": "Cash",
				"external_draft_id": "42",
				"external_order_id": None,
				"sync_status": "Synced",
				"last_sync_attempt": now_datetime(),
			},
		)

	def saved(self, *fields):
		return frappe.db.get_value("Field Order", self.order.name, list(fields), as_dict=True)

	def link(self, store_payment=None, confirmed=True):
		"""Run ``link_completed_drafts`` with quotation 42 confirmed (or not) in Odoo."""
		conn = MagicMock()
		conn.settings.platform = "Odoo"
		conn.get_completed_drafts.return_value = {"42": "42"} if confirmed else {}
		conn.get_store_payment.return_value = store_payment
		quiet = [
			patch.object(orders, name)
			for name in ("enqueue_create_entries", "enqueue_order_confirmation", "notify_order_synced", "notify_sync_result")
		]
		with patch.object(orders, "get_connector", return_value=conn), patch.object(frappe.db, "commit"), patch(
			"field_sales_odoo.payments.store_payments.notify_payment_received"
		), patch.object(orders, "enqueue_mark_store_paid") as enqueue:
			for p in quiet:
				p.start()
			try:
				orders.link_completed_drafts()
			finally:
				for p in quiet:
					p.stop()
		return conn, enqueue

	# -- linking ------------------------------------------------------------------

	def test_paid_in_agamsale_marks_the_confirmed_order_paid(self):
		conn, enqueue = self.link()
		self.assertEqual(self.saved("external_order_id").external_order_id, "42")
		conn.get_store_payment.assert_called_once_with("42")
		enqueue.assert_called_once_with(self.order.name)

	def test_paid_in_agamsale_and_on_odoo_is_only_noted(self):
		payment = {"amount": self.total, "currency": "INR", "method": "Cash", "reference": "INV/1", "paid_at": None}
		_conn, enqueue = self.link(store_payment=payment)
		self.assertIsNotNone(self.saved("store_marked_paid_on").store_marked_paid_on)
		enqueue.assert_not_called()
		self.assertFalse(frappe.db.exists("Payment Transaction", {"reference_order": self.order.name, "source": "Store Checkout"}))

	def test_paid_on_the_portal_marks_the_field_order_paid(self):
		frappe.db.set_value(
			"Field Order", self.order.name, {"payment_status": "Unpaid", "amount_paid": 0, "paid_on": None, "manual_payment_method": None}
		)
		payment = {"amount": self.total, "currency": "INR", "method": "Stripe", "reference": "T-9", "paid_at": "2026-11-17 05:00:00"}
		_conn, enqueue = self.link(store_payment=payment)
		o = self.saved("payment_status", "amount_paid", "store_marked_paid_on")
		self.assertEqual((o.payment_status, o.amount_paid), ("Paid", self.total))
		self.assertIsNotNone(o.store_marked_paid_on)
		enqueue.assert_not_called()
		self.assertTrue(
			frappe.db.exists("Payment Transaction", {"reference_order": self.order.name, "source": "Store Checkout", "method": "Stripe"})
		)

	def test_quotation_not_confirmed_yet_changes_nothing(self):
		conn, enqueue = self.link(confirmed=False)
		self.assertIsNone(self.saved("external_order_id").external_order_id)
		conn.get_store_payment.assert_not_called()
		enqueue.assert_not_called()

	def test_store_error_reading_the_payment_still_queues_marking(self):
		conn = MagicMock()
		conn.get_store_payment.side_effect = ConnectorError("down", code="NETWORK_ERROR")
		frappe.db.set_value("Field Order", self.order.name, "external_order_id", "42")
		with patch.object(orders, "enqueue_mark_store_paid") as enqueue:
			orders._carry_draft_payment(conn, self.order.name, "42")
		enqueue.assert_called_once_with(self.order.name)

	# -- marking the Odoo order paid -------------------------------------------------

	def test_confirmed_quotation_is_marked_like_a_confirmed_order(self):
		frappe.db.set_value("Field Order", self.order.name, "external_order_id", "42")
		conn = MagicMock()
		conn.mark_order_paid.return_value = {"financial_status": "paid", "already_paid": False}
		with patch.object(orders, "get_connector", return_value=conn):
			orders.mark_store_order_paid(self.order.name)
		conn.mark_order_paid.assert_called_once()
		self.assertIsNotNone(self.saved("store_marked_paid_on").store_marked_paid_on)

	def test_unconfirmed_quotation_is_not_marked(self):
		conn = MagicMock()
		with patch.object(orders, "get_connector", return_value=conn):
			orders.mark_store_order_paid(self.order.name)
		conn.mark_order_paid.assert_not_called()

	def test_hourly_retry_includes_confirmed_quotations(self):
		frappe.db.set_value("Field Order", self.order.name, "external_order_id", "42")
		with patch.object(orders, "enqueue_mark_store_paid") as enqueue:
			orders.retry_store_payments()
		self.assertIn(self.order.name, [c.args[0] for c in enqueue.call_args_list])
