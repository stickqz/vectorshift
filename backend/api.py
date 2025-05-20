from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware

from integrations.airtable import (
    authorize_airtable,
    get_items_airtable,
    oauth2callback_airtable,
    get_airtable_credentials
)
from integrations.notion import (
    authorize_notion,
    get_items_notion,
    oauth2callback_notion,
    get_notion_credentials
)
from integrations.hubspot import (
    authorize_hubspot,
    get_hubspot_credentials,
    get_items_hubspot,
    oauth2callback_hubspot
)


def _create_app():
    """Create and configure FastAPI application."""
    app = FastAPI(title="Integrations API")

    # CORS config
    origins = ["http://localhost:3000"]  # React app address
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    return app


app = _create_app()


@app.get('/')
def read_root():
    """Health check endpoint."""
    return {'status': 'ok'}


# Airtable Integration Routes
@app.post('/integrations/airtable/authorize')
async def authorize_airtable_integration(
    user_id: str = Form(...),
    org_id: str = Form(...)
):
    """Initialize Airtable OAuth flow."""
    return await authorize_airtable(user_id, org_id)


@app.get('/integrations/airtable/oauth2callback')
async def oauth2callback_airtable_integration(request: Request):
    """Handle Airtable OAuth callback."""
    return await oauth2callback_airtable(request)


@app.post('/integrations/airtable/credentials')
async def get_airtable_credentials_integration(
    user_id: str = Form(...),
    org_id: str = Form(...)
):
    """Retrieve Airtable credentials."""
    return await get_airtable_credentials(user_id, org_id)


@app.post('/integrations/airtable/load')
async def get_airtable_items(credentials: str = Form(...)):
    """Load Airtable items."""
    return await get_items_airtable(credentials)


# Notion Integration Routes
@app.post('/integrations/notion/authorize')
async def authorize_notion_integration(
    user_id: str = Form(...),
    org_id: str = Form(...)
):
    """Initialize Notion OAuth flow."""
    return await authorize_notion(user_id, org_id)


@app.get('/integrations/notion/oauth2callback')
async def oauth2callback_notion_integration(request: Request):
    """Handle Notion OAuth callback."""
    return await oauth2callback_notion(request)


@app.post('/integrations/notion/credentials')
async def get_notion_credentials_integration(
    user_id: str = Form(...),
    org_id: str = Form(...)
):
    """Retrieve Notion credentials."""
    return await get_notion_credentials(user_id, org_id)


@app.post('/integrations/notion/load')
async def get_notion_items(credentials: str = Form(...)):
    """Load Notion items."""
    return await get_items_notion(credentials)


# HubSpot Integration Routes
@app.post('/integrations/hubspot/authorize')
async def authorize_hubspot_integration(
    user_id: str = Form(...),
    org_id: str = Form(...)
):
    """Initialize HubSpot OAuth flow."""
    return await authorize_hubspot(user_id, org_id)


@app.get('/integrations/hubspot/oauth2callback')
async def oauth2callback_hubspot_integration(request: Request):
    """Handle HubSpot OAuth callback."""
    return await oauth2callback_hubspot(request)


@app.post('/integrations/hubspot/credentials')
async def get_hubspot_credentials_integration(
    user_id: str = Form(...),
    org_id: str = Form(...)
):
    """Retrieve HubSpot credentials."""
    return await get_hubspot_credentials(user_id, org_id)


@app.post('/integrations/hubspot/load')
async def get_hubspot_items(credentials: str = Form(...)):
    """Load HubSpot items."""
    return await get_items_hubspot(credentials)
