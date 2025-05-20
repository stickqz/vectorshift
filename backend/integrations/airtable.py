import datetime
import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import hashlib
import requests
from integrations.integration_item import IntegrationItem
import redis_client
from config import airtable


def _get_encoded_client_credentials():
    creds = f"{airtable['client_id']}:{airtable['client_secret']}"
    return base64.b64encode(creds.encode()).decode()


def _create_state_data(user_id, org_id):
    """Create state data for OAuth flow."""
    return {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }


def _generate_code_challenge():
    """Generate PKCE code challenge for OAuth flow."""
    code_verifier = secrets.token_urlsafe(32)
    m = hashlib.sha256()
    m.update(code_verifier.encode('utf-8'))
    code_challenge = base64.urlsafe_b64encode(m.digest()).decode('utf-8').replace('=', '')
    return code_verifier, code_challenge


def _get_auth_url(encoded_state, code_challenge):
    """Construct Airtable authorization URL."""
    params = {
        'client_id': airtable['client_id'],
        'response_type': 'code',
        'owner': 'user',
        'redirect_uri': airtable['redirect_uri'],
        'state': encoded_state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'scope': airtable['scopes']
    }
    query_string = '&'.join(f"{k}={v}" for k, v in params.items())
    return f"{airtable['auth_url']}?{query_string}"


async def authorize_airtable(user_id, org_id):
    """Initialize OAuth flow for Airtable."""
    state_data = _create_state_data(user_id, org_id)
    encoded_state = base64.urlsafe_b64encode(
        json.dumps(state_data).encode('utf-8')
    ).decode('utf-8')

    code_verifier, code_challenge = _generate_code_challenge()
    auth_url = _get_auth_url(encoded_state, code_challenge)

    await asyncio.gather(
        redis_client.add_key_value(
            f'airtable_state:{org_id}:{user_id}',
            json.dumps(state_data),
            expire=600
        ),
        redis_client.add_key_value(
            f'airtable_verifier:{org_id}:{user_id}',
            code_verifier,
            expire=600
        )
    )

    return auth_url


def _get_close_window_response():
    """Return HTML response to close the OAuth window."""
    return HTMLResponse(content="""
        <html>
            <script>
                window.close();
            </script>
        </html>
    """)


async def oauth2callback_airtable(request: Request):
    """Handle OAuth callback from Airtable."""
    if request.query_params.get('error'):
        raise HTTPException(
            status_code=400,
            detail=request.query_params.get('error_description')
        )

    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    state_data = json.loads(
        base64.urlsafe_b64decode(encoded_state).decode('utf-8')
    )

    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')
    original_state = state_data.get('state')

    saved_state, code_verifier = await asyncio.gather(
        redis_client.get_value(f'airtable_state:{org_id}:{user_id}'),
        redis_client.get_value(f'airtable_verifier:{org_id}:{user_id}')
    )

    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    encoded_credentials = _get_encoded_client_credentials()

    async with httpx.AsyncClient() as client:
        response, _, _ = await asyncio.gather(
            client.post(
                airtable['token_url'],
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': airtable['redirect_uri'],
                    'client_id': airtable['client_id'],
                    'code_verifier': code_verifier.decode('utf-8')
                },
                headers={
                    'Authorization': f'Basic {encoded_credentials}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            ),
            redis_client.delete_key(f'airtable_state:{org_id}:{user_id}'),
            redis_client.delete_key(f'airtable_verifier:{org_id}:{user_id}')
        )

    await redis_client.add_key_value(
        f'airtable_credentials:{org_id}:{user_id}',
        json.dumps(response.json()),
        expire=600
    )

    return _get_close_window_response()


async def get_airtable_credentials(user_id, org_id):
    """Retrieve Airtable credentials from Redis."""
    credentials = await redis_client.get_value(f'airtable_credentials:{org_id}:{user_id}')
    
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    
    credentials = json.loads(credentials)
    await redis_client.delete_key(f'airtable_credentials:{org_id}:{user_id}')

    return credentials


def _create_integration_item_metadata_object(
    response_json: str,
    item_type: str,
    parent_id=None,
    parent_name=None
) -> IntegrationItem:
    """Create IntegrationItem from Airtable response."""
    parent_id = None if parent_id is None else f"{parent_id}_Base"
    
    return IntegrationItem(
        id=f"{response_json.get('id', None)}_{item_type}",
        name=response_json.get('name', None),
        type=item_type,
        parent_id=parent_id,
        parent_path_or_name=parent_name
    )


async def _fetch_items(access_token: str, url: str, aggregated_response: list, offset=None):
    """Fetch items from Airtable API with pagination."""
    params = {'offset': offset} if offset is not None else {}
    headers = {'Authorization': f'Bearer {access_token}'}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return

    data = response.json()
    results = data.get('bases', {})
    offset = data.get('offset')

    aggregated_response.extend(results)

    if offset is not None:
        await _fetch_items(access_token, url, aggregated_response, offset)


async def _fetch_tables_for_base(client: httpx.AsyncClient, base: dict, access_token: str) -> list[IntegrationItem]:
    """Fetch tables for a specific base."""
    tables_url = f"{airtable['api_base_url']}/meta/bases/{base.get('id')}/tables"
    response = await client.get(
        tables_url,
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    items = []
    if response.status_code == 200:
        tables = response.json()['tables']
        items.extend([
            _create_integration_item_metadata_object(
                table,
                'Table',
                base.get('id'),
                base.get('name')
            )
            for table in tables
        ])
    return items


async def get_items_airtable(credentials) -> list[IntegrationItem]:
    """Fetch and process items from Airtable."""
    print(credentials)

    credentials = json.loads(credentials)
    access_token = credentials.get('access_token')
    url = f"{airtable['api_base_url']}/meta/bases"
    
    bases = []
    await _fetch_items(access_token, url, bases)
    
    items = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Create base items
            base_items = [
                _create_integration_item_metadata_object(base, 'Base')
                for base in bases
            ]
            items.extend(base_items)
            
            # Fetch tables for all bases concurrently
            table_tasks = [
                _fetch_tables_for_base(client, base, access_token)
                for base in bases
            ]
            table_results = await asyncio.gather(*table_tasks)
            
            # Extend items with all table results
            for table_items in table_results:
                items.extend(table_items)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail='Request to Airtable timed out')
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f'Failed to connect to Airtable: {str(e)}')

    return items
