# Field Sales Odoo Connector

Odoo connector app for Field Sales.

Enables Field Sales to sync products, stock, customers, and orders with an Odoo instance via Odoo's stateless JSON-RPC endpoint (`/jsonrpc`) using API key authentication.

## Installation

```bash
bench get-app field_sales_odoo
bench --site [your-site] install-app field_sales_odoo
```

## Features

- **Products**: Synchronize products from `product.product`, standard and sales prices, and tracking flags.
- **Stock**: Warehouse-scoped inventory from `stock.warehouse` (or single pseudo-location "odoo" when Inventory app is absent).
- **Customers**: Create and update Odoo partners (`res.partner`) from Retailer records.
- **Orders**: Push submitted Field Orders as Odoo sale orders (`sale.order`) in either Draft (`draft`) or Confirmed (`sale`) state.
- **Shop Settings**: Match company currency and user time zone from Odoo.
- **Store changes**: Odoo sends no webhooks, so every 15 minutes the app asks Odoo which sale orders (order, invoice or payment), products and stock changed and applies them as the other platforms' webhooks do: commission follows paid / delivered / cancelled / refunded orders, and prices, archiving and stock follow the store (`sync/polling.py`).

## License

MIT
