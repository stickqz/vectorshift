import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import requests

from integrations.integration_item import IntegrationItem
import redis_client
from config import notion


def _get_encoded_client_credentials():
    """Get base64 encoded client credentials for Notion API."""
    credentials = f"{notion['client_id']}:{notion['client_secret']}"
    return base64.b64encode(credentials.encode()).decode()


def _create_state_data(user_id, org_id):
    """Create state data for OAuth flow."""
    return {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }


def _get_auth_url(encoded_state):
    """Construct Notion authorization URL."""
    params = {
        'client_id': notion['client_id'],
        'response_type': 'code',
        'owner': 'user',
        'redirect_uri': notion['redirect_uri'],
        'state': encoded_state
    }
    query_string = '&'.join(f"{k}={v}" for k, v in params.items())
    return f"{notion['auth_url']}?{query_string}"


async def authorize_notion(user_id, org_id):
    """Initialize OAuth flow for Notion."""
    state_data = _create_state_data(user_id, org_id)

    encoded_state = base64.urlsafe_b64encode(
        json.dumps(state_data).encode('utf-8')
    ).decode('utf-8')

    # Save original JSON to Redis
    await redis_client.add_key_value(
        f'notion_state:{org_id}:{user_id}',
        json.dumps(state_data),
        expire=600
    )

    # Build auth URL
    auth_url = _get_auth_url(encoded_state)
    print("Authorization URL:", auth_url)
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


async def oauth2callback_notion(request: Request):
    """Handle OAuth callback from Notion."""
    if request.query_params.get('error'):
        raise HTTPException(
            status_code=400,
            detail=request.query_params.get('error')
        )

    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    state_data = json.loads(
        base64.urlsafe_b64decode(encoded_state).decode('utf-8')
    )

    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')
    original_state = state_data.get('state')

    saved_state = await redis_client.get_value(f'notion_state:{org_id}:{user_id}')

    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    encoded_credentials = _get_encoded_client_credentials()
    
    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                notion['token_url'],
                json={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': notion['redirect_uri']
                },
                headers={
                    'Authorization': f'Basic {encoded_credentials}',
                    'Content-Type': 'application/json',
                }
            ),
            redis_client.delete_key(f'notion_state:{org_id}:{user_id}')
        )

    await redis_client.add_key_value(
        f'notion_credentials:{org_id}:{user_id}',
        json.dumps(response.json()),
        expire=600
    )
    
    return _get_close_window_response()


async def get_notion_credentials(user_id, org_id):
    """Retrieve Notion credentials from Redis."""
    credentials = await redis_client.get_value(f'notion_credentials:{org_id}:{user_id}')
    
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    
    credentials = json.loads(credentials)
    await redis_client.delete_key(f'notion_credentials:{org_id}:{user_id}')

    return credentials


def _recursive_dict_search(data, target_key):
    """Recursively search for a key in a dictionary of dictionaries."""
    if target_key in data:
        return data[target_key]

    for value in data.values():
        if isinstance(value, dict):
            result = _recursive_dict_search(value, target_key)
            if result is not None:
                return result
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = _recursive_dict_search(item, target_key)
                    if result is not None:
                        return result
    return None


def _get_item_name(response_json):
    """Extract name from Notion response."""
    name = _recursive_dict_search(response_json['properties'], 'content')
    if name is None:
        name = _recursive_dict_search(response_json, 'content')
    if name is None:
        name = 'multi_select'
    return f"{response_json['object']} {name}"


def _get_parent_id(response_json):
    """Extract parent ID from Notion response."""
    parent_type = response_json['parent']['type']
    if parent_type == 'workspace':
        return None
    return response_json['parent'].get(parent_type)


def _create_integration_item_metadata_object(response_json: str) -> IntegrationItem:
    """Create IntegrationItem from Notion response."""
    return IntegrationItem(
        id=response_json['id'],
        type=response_json['object'],
        name=_get_item_name(response_json),
        creation_time=response_json['created_time'],
        last_modified_time=response_json['last_edited_time'],
        parent_id=_get_parent_id(response_json)
    )


async def get_items_notion(credentials) -> list[IntegrationItem]:
    """Fetch and process items from Notion."""
    credentials = json.loads(credentials)
    access_token = credentials.get('access_token')

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{notion['api_base_url']}/search",
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Notion-Version': notion['api_version'],
                }
            )
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail='Request to Notion timed out')
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f'Failed to connect to Notion: {str(e)}')

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    results = response.json()['results']
    seen_ids = set()
    unique_results = []
    for result in results:
        rid = result.get('id')
        if rid and rid not in seen_ids:
            seen_ids.add(rid)
            unique_results.append(result)

    return [
        _create_integration_item_metadata_object(result)
        for result in unique_results
    ]
