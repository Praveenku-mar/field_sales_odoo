app_name = "field_sales_odoo"
app_title = "Field Sales Odoo"
app_publisher = "Agamnxt Technologies"
app_description = "Odoo Connector for Field Sales"
app_email = "praveenkumar@agamnxt.com"
app_license = "mit"

required_apps = ["field_sales"]

field_sales_connectors = {
	"Odoo": "field_sales_odoo.connector.OdooConnector",
}
