OFFLINE SETUP INSTRUCTIONS
==========================

1. Chart.js
   - Location: static/vendor/js/chart.js
   - Status: Fully downloaded.

2. Font Awesome
   - Location: static/vendor/css/fontawesome.all.min.css
   - Webfonts: static/vendor/webfonts/ (Downloaded: fa-solid-900.woff2, fa-regular-400.woff2, fa-brands-400.woff2)
   - Status: Core icons should work offline. If you need other weights/styles, please download the full Font Awesome Free package.

3. Google Fonts (Inter)
   - Location: static/vendor/css/inter.css
   - Status: CSS downloaded, BUT it refers to online 'fonts.gstatic.com' URLs.
   - ACTION REQUIRED: In a strictly closed network, these requests will fail.
     a) Download the static 'Inter' font files (TTF/WOFF2) manually.
     b) Place them in `static/vendor/fonts`.
     c) Edit `inter.css` to point `src` to these local files.
     d) Alternatively, clear `inter.css` to rely on the system font fallback defined in dashboard.css.
