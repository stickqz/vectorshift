import json
import datetime
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import requests
from integrations.integration_item import IntegrationItem
import redis_client
from config import hubspot


def _get_close_window_response():
    """Return HTML response to close the OAuth window."""
    return HTMLResponse(content="""
        <html>
            <script>
                window.close();
            </script>
        </html>
    """)


def _create_state_data(user_id, org_id):
    """Create state data for OAuth flow."""
    return {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }


def _get_auth_url(encoded_state):
    """Construct HubSpot authorization URL."""
    params = {
        'client_id': hubspot['client_id'],
        'redirect_uri': hubspot['redirect_uri'],
        'scope': hubspot['scopes'],
        'state': encoded_state
    }

    query_string = '&'.join(f"{k}={v}" for k, v in params.items())
    return f"{hubspot['auth_url']}?{query_string}"


async def authorize_hubspot(user_id, org_id):
    """Initialize OAuth flow for HubSpot."""
    state_data = _create_state_data(user_id, org_id)
    encoded_state = base64.urlsafe_b64encode(
        json.dumps(state_data).encode('utf-8')
    ).decode('utf-8')
    
    await redis_client.add_key_value(
        f'hubspot_state:{org_id}:{user_id}',
        json.dumps(state_data),
        expire=600
    )

    return _get_auth_url(encoded_state)


async def oauth2callback_hubspot(request: Request):
    """Handle OAuth callback from HubSpot."""
    
    if request.query_params.get('error'):
        error = request.query_params.get('error')
        error_description = request.query_params.get('error_description')
        print(f"OAuth error: {error} - {error_description}")
        raise HTTPException(
            status_code=400,
            detail=error_description or error
        )
    
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    
    if not code or not encoded_state:
        print("Missing code or state in callback")
        raise HTTPException(
            status_code=400,
            detail="Missing required parameters: code or state"
        )
    
    try:
        state_data = json.loads(
            base64.urlsafe_b64decode(encoded_state).decode('utf-8')
        )
    except Exception as e:
        print(f"Failed to decode state: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter"
        )

    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')
    original_state = state_data.get('state')

    if not all([user_id, org_id, original_state]):
        print("Missing required state data:", state_data)
        raise HTTPException(
            status_code=400,
            detail="Invalid state data"
        )

    saved_state = await redis_client.get_value(f'hubspot_state:{org_id}:{user_id}')
    print("Saved state from Redis:", saved_state)

    if not saved_state:
        print("No saved state found in Redis")
        raise HTTPException(status_code=400, detail='State not found in Redis')

    saved_state_data = json.loads(saved_state)
    if original_state != saved_state_data.get('state'):
        print("State mismatch:", {
            "original": original_state,
            "saved": saved_state_data.get('state')
        })
        raise HTTPException(status_code=400, detail='State does not match.')

    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                hubspot['token_url'],
                data={
                    'grant_type': 'authorization_code',
                    'client_id': hubspot['client_id'],
                    'client_secret': hubspot['client_secret'],
                    'redirect_uri': hubspot['redirect_uri'],
                    'code': code
                }
            )
            print("Token response status:", token_response.status_code)
            print("Token response:", token_response.text)

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=token_response.status_code,
                    detail=token_response.text
                )

            await redis_client.add_key_value(
                f'hubspot_credentials:{org_id}:{user_id}',
                token_response.text,
                expire=600
            )
            await redis_client.delete_key(f'hubspot_state:{org_id}:{user_id}')
    except Exception as e:
        print(f"Error during token exchange: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to exchange code for token: {str(e)}"
        )
    
    return _get_close_window_response()


async def get_hubspot_credentials(user_id, org_id):
    """Retrieve HubSpot credentials from Redis."""
    credentials = await redis_client.get_value(f'hubspot_credentials:{org_id}:{user_id}')
    
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    
    credentials = json.loads(credentials)
    await redis_client.delete_key(f'hubspot_credentials:{org_id}:{user_id}')

    return credentials


def _get_item_name(response_json, item_type):
    """Extract name from HubSpot response."""
    properties = response_json.get('properties', {})
    if item_type == 'contact':
        firstname = properties.get('firstname', '')
        lastname = properties.get('lastname', '')
        return f"{firstname} {lastname}".strip() or properties.get('name', '')
    return properties.get('name', '')


def _create_integration_item_metadata_object(response_json, item_type):
    """Create IntegrationItem from HubSpot response."""
    return IntegrationItem(
        id=str(response_json.get('id')),
        type=item_type,
        name=_get_item_name(response_json, item_type),
        creation_time=response_json.get('createdAt'),
        last_modified_time=response_json.get('updatedAt'),
        url=f"https://app.hubspot.com/{item_type}s/{response_json.get('id')}"
    )


async def get_items_hubspot(credentials):
    """Fetch contacts and companies from HubSpot."""
    credentials = json.loads(credentials)
    access_token = credentials.get('access_token')

    if not access_token:
        raise HTTPException(status_code=400, detail='Invalid credentials')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    async with httpx.AsyncClient() as client:
        # Fetch contacts and companies concurrently
        contacts_task = client.get(
            f"{hubspot['api_base_url']}/crm/v3/objects/contacts",
            headers=headers
        )
        companies_task = client.get(
            f"{hubspot['api_base_url']}/crm/v3/objects/companies",
            headers=headers
        )
        # Wait for both requests to complete
        contacts_response, companies_response = await asyncio.gather(contacts_task, companies_task)

    if contacts_response.status_code != 200:
        raise HTTPException(
            status_code=contacts_response.status_code,
            detail=contacts_response.text
        )

    if companies_response.status_code != 200:
        raise HTTPException(
            status_code=companies_response.status_code,
            detail=companies_response.text
        )

    items = []
    # Process contacts
    for contact in contacts_response.json().get('results', []):
        items.append(_create_integration_item_metadata_object(contact, 'contact'))
    # Process companies
    for company in companies_response.json().get('results', []):
        items.append(_create_integration_item_metadata_object(company, 'company'))
    return items