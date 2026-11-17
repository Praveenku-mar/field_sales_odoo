// Sidebar navigation. An item has `route` (an SPA page) or `href` (a desk page).
// `count` names a key returned by frontend_api.get_sidebar_counts; `roles` hides the item
// from everyone else, `feature: 'commission'` hides it when commission is off (session.canSee;
// the router and the server check again). `retailerOnly` is for the customer login alone:
// a role check would leak it (Administrator holds every role).
export const MANAGERS = ['System Manager', 'Sales Manager']

// Staff pages: everyone who works the app. A customer login (Field Sales Retailer)
// holds none of these roles and gets the customer items below instead.
export const STAFF = ['System Manager', 'Sales Manager', 'Field Sales Rep']

export const NAV_ITEMS = [
  { label: 'Dashboard', route: 'Dashboard', icon: 'lucide-layout-dashboard', roles: STAFF },
  { label: 'Shops', route: 'Retailers', icon: 'lucide-store', count: 'retailers', roles: STAFF },
  { label: 'Visits', route: 'Visits', icon: 'lucide-map-pin-check', roles: STAFF },
  {
    label: 'Orders',
    route: 'Orders',
    icon: 'lucide-shopping-cart',
    count: 'failed_orders',
    countTheme: 'red',
    countTooltip: 'Orders that failed to sync',
    roles: STAFF,
  },
  { label: 'Products', route: 'Products', icon: 'lucide-package', roles: STAFF },
  // Everyone: a rep sees themselves and their team (Sales Rep permission_query_conditions).
  { label: 'Sales Reps', route: 'SalesReps', icon: 'lucide-user-round', roles: STAFF },
  // Everyone: a rep sees their own commission; managers also see the team and statements.
  { label: 'Commission', route: 'Commission', icon: 'lucide-wallet', feature: 'commission', roles: STAFF },
  { label: 'Reports', route: 'Reports', icon: 'lucide-chart-column', roles: MANAGERS },
  { label: 'Sync Log', route: 'SyncLogs', icon: 'lucide-scroll-text', roles: MANAGERS },
  { label: 'Sync Failures', route: 'SyncFailures', icon: 'lucide-triangle-alert', roles: MANAGERS },
  { label: 'Settings', route: 'Settings', icon: 'lucide-settings', roles: MANAGERS },
  // The customer login: its own orders, read only.
  { label: 'My Orders', route: 'MyOrders', icon: 'lucide-shopping-cart', retailerOnly: true },
]

// Listed on the Reports page.
export const REPORT_LINKS = [
  {
    label: 'Rep Performance',
    description: 'Visits, orders and target achievement per sales rep.',
    route: { name: 'RepPerformance' },
    icon: 'lucide-chart-column',
    roles: MANAGERS,
  },
  {
    label: 'Rep Commission',
    description: 'Sales, earned, pending, reversed, override, paid and unpaid commission per rep.',
    route: { name: 'RepCommission' },
    icon: 'lucide-wallet',
    roles: MANAGERS,
    feature: 'commission',
  },
]

// Records with a page in this app (route :name is the docname). Anything else opens in the desk.
const DOCTYPE_ROUTES = {
  'Field Order': 'Order',
  Retailer: 'Retailer',
  Visit: 'Visit',
  'Platform Product': 'Product',
  'Sales Rep': 'SalesRep',
  'Commission Statement': 'CommissionStatement',
  'Sync Log': 'SyncLogEntry',
}

/** Where a notification's document lives: `{ route }` inside the SPA, else `{ href }` in the desk. */
export function documentTarget(doctype, name) {
  if (!doctype || !name) return null
  const routeName = DOCTYPE_ROUTES[doctype]
  if (routeName) return { route: { name: routeName, params: { name } } }
  return { href: `/app/${doctype.toLowerCase().replace(/\s+/g, '-')}/${encodeURIComponent(name)}` }
}

// Odoo-style top menu: app sections, each a link (one page) or a dropdown (several).
// Items are NAV_ITEMS routes or REPORT_LINKS route names; the same visibility rules apply
// (session.canSee), and a section with nothing visible is hidden.
export const MENU_SECTIONS = [
  { label: 'Dashboard', items: ['Dashboard'] },
  { label: 'Sales', items: ['Orders', 'Retailers', 'Visits'] },
  { label: 'Products', items: ['Products'] },
  { label: 'Team', items: ['SalesReps', 'Commission'] },
  { label: 'Reporting', items: ['RepPerformance', 'RepCommission', '-', 'SyncLogs', 'SyncFailures'] },
  { label: 'Configuration', items: ['Settings'] },
  { label: 'My Orders', items: ['MyOrders'] },
]

/** MENU_SECTIONS resolved for this user: [{ label, items: [{ label, route, count?, ... } | '-'] }] */
export function menuSections(canSee) {
  const byRoute = Object.fromEntries([
    ...NAV_ITEMS.map((item) => [item.route, item]),
    ...REPORT_LINKS.map((link) => [link.route.name, { ...link, route: link.route.name }]),
  ])
  return MENU_SECTIONS.map((section) => {
    const items = section.items.map((key) => (key === '-' ? '-' : byRoute[key])).filter((item) => item === '-' || (item && canSee(item)))
    // No separator at either end or twice in a row.
    const tidy = items.filter((item, i) => item !== '-' || (i > 0 && i < items.length - 1 && items[i - 1] !== '-'))
    return { ...section, items: tidy }
  }).filter((section) => section.items.some((item) => item !== '-'))
}
