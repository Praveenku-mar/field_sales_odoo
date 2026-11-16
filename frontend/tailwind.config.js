import frappeUIPreset, { content as frappeUIContent } from 'frappe-ui/tailwind'

export default {
  presets: [frappeUIPreset],
  content: ['./index.html', './src/**/*.{vue,js,ts}', ...frappeUIContent],
  theme: {
    extend: {
      // Odoo 17/18 look: page background and borders (src/theme/odoo.css has the rest).
      colors: {
        desk: { bg: '#F9FAFB', border: '#D8DADD' },
        odoo: {
          primary: '#714B67',
          'primary-dark': '#5C3D54',
          action: '#017E84',
          'action-dark': '#01585C',
          text: '#374151',
          strong: '#111827',
          muted: '#5F636F',
          hover: '#E7E9ED',
          line: '#D8DADD',
        },
      },
      height: { topbar: '46px' },
    },
  },
}
