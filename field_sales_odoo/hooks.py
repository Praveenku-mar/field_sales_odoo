app_name = "field_sales_odoo"
app_title = "Agamsale"
app_publisher = "Agamnxt Technologies"
app_description = "Agamsale app dedicated to Odoo stores"
app_email = "praveenkumar@agamnxt.com"
app_license = "mit"

use_json_request_body = True

add_to_apps_screen = [
	{
		"name": "field_sales_odoo",
		"logo": "/assets/field_sales_odoo/images/agamsale-logo.png",
		"title": "Agamsale",
		"route": "/fieldsales",
		"has_permission": "field_sales_odoo.www.fieldsales.has_app_access",
	}
]

# Serve the Vue app shell for its deep links (/fieldsales/orders, a refresh on any page)
# and the short alias /fs.
website_route_rules = [
	{"from_route": "/fieldsales/<path:app_path>", "to_route": "fieldsales"},
	{"from_route": "/fs", "to_route": "fieldsales"},
	{"from_route": "/fs/<path:app_path>", "to_route": "fieldsales"},
]

permission_query_conditions = {
	"Visit": "field_sales_odoo.permissions.visit_query",
	"Sales Rep": "field_sales_odoo.permissions.sales_rep_query",
	"Field Order": "field_sales_odoo.permissions.field_order_query",
	"Retailer": "field_sales_odoo.permissions.retailer_query",
	"Commission Entry": "field_sales_odoo.permissions.commission_entry_query",
	"Commission Statement": "field_sales_odoo.permissions.commission_statement_query",
}

has_permission = {
	"Visit": "field_sales_odoo.permissions.visit_has_permission",
	"Sales Rep": "field_sales_odoo.permissions.sales_rep_has_permission",
	"Field Order": "field_sales_odoo.permissions.field_order_has_permission",
	"Retailer": "field_sales_odoo.permissions.retailer_has_permission",
	"Commission Entry": "field_sales_odoo.permissions.commission_entry_has_permission",
	"Commission Statement": "field_sales_odoo.permissions.commission_statement_has_permission",
}

fixtures = [
	{"dt": "Print Format", "filters": [["name", "in", ["Field Sales Order", "Field Sales Invoice"]]]},
]

doc_events = {
	# Push bell notifications made by push.notify.notify_users to the mobile app.
	"Notification Log": {"after_insert": "field_sales_odoo.push.notify.on_notification_log_insert"},
}

# Background jobs. Each job checks its own switch (Store Connection enabled, sync frequency,
# Razorpay / commission on, anonymise days > 0), so a site that has not set one up does nothing.
scheduler_events = {
	# Purge Success Sync Logs older than 30 days, Failed ones after failed_log_retention_days.
	"daily": [
		"field_sales_odoo.field_sales_odoo.doctype.sync_log.sync_log.clear_old_logs",
		# Keep the site's currency and time zone the same as the store's.
		"field_sales_odoo.sync.shop_settings.scheduled_sync",
		# Store Connection retailer_inactive_anonymise_days (0 = off).
		"field_sales_odoo.utils.anonymise.anonymise_inactive_retailers",
	],
	# Razorpay payment links whose webhook never arrived (Link Sent, last 7 days, 50 a run).
	"hourly": [
		"field_sales_odoo.payments.razorpay.reconcile_open_links",
		# Confirmed store orders paid on Razorpay that the store does not show as paid yet.
		"field_sales_odoo.sync.orders.retry_store_payments",
	],
	# Ticks every 30 minutes; scheduled_sync itself honours Store Connection's sync frequency.
	"cron": {
		"*/30 * * * *": [
			"field_sales_odoo.sync.products.scheduled_sync",
			# Record the order id of drafts completed on the store after they synced.
			"field_sales_odoo.sync.orders.link_completed_drafts",
		],
		# Re-push Field Orders that failed (up to 5 attempts) or lost their job.
		"*/15 * * * *": [
			"field_sales_odoo.sync.orders.retry_failed_orders",
		],
		# Daily team summary to each manager, in the system timezone.
		"0 20 * * *": [
			"field_sales_odoo.daily_summary.send_daily_summary",
		],
		# Draft Commission Statements for last month, on the 1st.
		"0 2 1 * *": [
			"field_sales_odoo.commission.statements.generate_monthly_statements",
		],
	},
}
