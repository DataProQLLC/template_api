"""Swagger UI with a version selector.

FastAPI's get_swagger_ui_html() only loads swagger-ui-bundle.js. The
"Select a definition" dropdown lives in StandaloneLayout, which is defined
in a SEPARATE file (swagger-ui-standalone-preset.js). Without that script
the page renders 'No layout defined for "StandaloneLayout"', so this module
emits its own HTML that loads both.
"""
import json

from fastapi.responses import HTMLResponse

_CDN = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5"


def swagger_ui_with_versions(
    *,
    title: str,
    urls: list[dict[str, str]],
    primary_name: str,
    cdn: str = _CDN,
) -> HTMLResponse:
    config = {
        "urls": urls,
        "urls.primaryName": primary_name,
        "dom_id": "#swagger-ui",
        "layout": "StandaloneLayout",
        "deepLinking": True,
        "displayRequestDuration": True,
        "tryItOutEnabled": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "persistAuthorization": True,
        "validatorUrl": None,
    }
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{cdn}/swagger-ui.css">
<style>
  /* Keep the definition selector, drop the Swagger branding. */
  .swagger-ui .topbar {{ background:#1b1b1f; }}
  .swagger-ui .topbar .topbar-wrapper a.link {{ display:none; }}
  .swagger-ui .topbar .download-url-wrapper .select-label span {{ color:#fff; }}
</style>
</head>
<body>
<div id="swagger-ui"></div>
<script src="{cdn}/swagger-ui-bundle.js"></script>
<!-- REQUIRED for StandaloneLayout / the version dropdown. -->
<script src="{cdn}/swagger-ui-standalone-preset.js"></script>
<script>
window.ui = SwaggerUIBundle(Object.assign({json.dumps(config)}, {{
  presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
  plugins: [SwaggerUIBundle.plugins.DownloadUrl]
}}));
</script>
</body>
</html>"""
    return HTMLResponse(html)