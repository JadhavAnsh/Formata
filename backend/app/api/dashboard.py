from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    html = """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Formata Dashboard</title>
      </head>
      <body>
        <h3>Formata Dashboard</h3>
        <p>Dash app is mounted at <a href="/dashboard/">/dashboard/</a></p>
      </body>
    </html>
    """
    return HTMLResponse(content=html)
