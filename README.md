# VectorShift Integrations

A web application that integrates with Airtable, Notion, and HubSpot to fetch and display data. Built with FastAPI and React.

**Status:** Airtable and Notion integrations are fully working, including OAuth authentication and data fetching. HubSpot is also supported.

## Quick Start

### Backend
```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
cd backend
pip install -r requirements.txt

# Configure
# Create .env with:
REDIS_URL=redis://localhost:6379
AIRTABLE_CLIENT_ID=your_client_id
AIRTABLE_CLIENT_SECRET=your_client_secret
NOTION_CLIENT_ID=your_client_id
NOTION_CLIENT_SECRET=your_client_secret
HUBSPOT_CLIENT_ID=your_client_id
HUBSPOT_CLIENT_SECRET=your_client_secret

# Run
uvicorn api:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Usage

1. Enter user ID and organization ID
2. Select integration (Airtable/Notion/HubSpot)
3. Click "Connect" and complete OAuth2 flow
4. View and interact with your data

## API Endpoints

Each integration (Airtable/Notion/HubSpot) provides:
- `POST /integrations/{service}/authorize` - Start OAuth
- `GET /integrations/{service}/oauth2callback` - OAuth callback
- `POST /integrations/{service}/credentials` - Get credentials
- `POST /integrations/{service}/load` - Load data

## Tech Stack

- **Backend**: FastAPI, Redis, OAuth2
- **Frontend**: React, Material-UI, Axios

## Development

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs