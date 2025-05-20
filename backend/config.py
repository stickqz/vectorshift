import os
from dotenv import load_dotenv

load_dotenv()

_base_url = 'http://localhost:8000/integrations'

redis = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379))
}

hubspot = {
    'client_id': os.getenv('HUBSPOT_CLIENT_ID'),
    'client_secret': os.getenv('HUBSPOT_CLIENT_SECRET'),
    'auth_url': 'https://app.hubspot.com/oauth/authorize',
    'token_url': 'https://api.hubapi.com/oauth/v1/token',
    'api_base_url': 'https://api.hubapi.com',
    'redirect_uri': f'{_base_url}/hubspot/oauth2callback',
    'scopes': 'crm.objects.contacts.read%20crm.objects.contacts.write%20crm.objects.companies.read%20crm.objects.companies.write%20oauth'
}

notion = {
    'client_id': os.getenv('NOTION_CLIENT_ID'),
    'client_secret': os.getenv('NOTION_CLIENT_SECRET'),
    'redirect_uri': f'{_base_url}/notion/oauth2callback',
    'auth_url': 'https://api.notion.com/v1/oauth/authorize',
    'token_url': 'https://api.notion.com/v1/oauth/token',
    'api_base_url': 'https://api.notion.com/v1',
    'api_version': '2022-06-28'
}

airtable = {
    'client_id': os.getenv('AIRTABLE_CLIENT_ID'),
    'client_secret': os.getenv('AIRTABLE_CLIENT_SECRET'),
    'redirect_uri': f'{_base_url}/airtable/oauth2callback',
    'auth_url': 'https://airtable.com/oauth2/v1/authorize',
    'token_url': 'https://api.airtable.com/oauth2/v1/token',
    'api_base_url': 'https://api.airtable.com/v0',
    'scopes': 'data.records:read%20data.records:write%20data.recordComments:read%20data.recordComments:write%20schema.bases:read%20schema.bases:write'
}
