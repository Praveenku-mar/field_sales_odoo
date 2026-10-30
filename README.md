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

## License

MIT
