import { useState, useEffect } from 'react';
import {
    Box,
    Button,
    CircularProgress,
    Stack
} from '@mui/material';
import axios from 'axios';


const NOTION_URL = 'http://localhost:8000/integrations/notion/';


export const NotionIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const [isDisconnecting, setIsDisconnecting] = useState(false);

    // Function to open OAuth in a new window
    const handleConnectClick = async () => {
        try {
            setIsConnecting(true);
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);
            const response = await axios.post(`${NOTION_URL}authorize`, formData);
            const authURL = response?.data;

            const newWindow = window.open(authURL, 'Notion Authorization', 'width=600, height=600');

            // Polling for the window to close
            const pollTimer = window.setInterval(() => {
                if (newWindow?.closed !== false) { 
                    window.clearInterval(pollTimer);
                    handleWindowClosed();
                }
            }, 200);
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail);
        }
    }

    // Function to handle disconnection
    const handleDisconnect = async () => {
        try {
            setIsDisconnecting(true);
            // Clear the credentials from the integration params
            setIntegrationParams(prev => ({ ...prev, credentials: null, type: null }));
            setIsConnected(false);
            setIsDisconnecting(false);
        } catch (e) {
            setIsDisconnecting(false);
            alert('Failed to disconnect: ' + e?.message);
        }
    }

    // Function to handle logic when the OAuth window closes
    const handleWindowClosed = async () => {
        try {
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);
            const response = await axios.post(`${NOTION_URL}credentials`, formData);
            const credentials = response.data; 
            if (credentials) {
                setIsConnecting(false);
                setIsConnected(true);
                setIntegrationParams(prev => ({ ...prev, credentials: credentials, type: 'Notion' }));
            }
            setIsConnecting(false);
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail);
        }
    }

    useEffect(() => {
        setIsConnected(integrationParams?.credentials ? true : false)
    }, [integrationParams]);

    return (
        <>
        <Box sx={{mt: 2}}>
            <Stack spacing={2} alignItems='center' sx={{mt: 2}}>
                {!isConnected ? (
                    <Button 
                        variant='contained' 
                        onClick={handleConnectClick}
                        color='primary'
                        disabled={isConnecting}
                    >
                        {isConnecting ? <CircularProgress size={20} /> : 'Connect to Notion'}
                    </Button>
                ) : (
                    <>
                        <Button 
                            variant='contained' 
                            color='success'
                            disabled
                        >
                            Notion Connected
                        </Button>
                        <Button 
                            variant='outlined' 
                            color='error'
                            onClick={handleDisconnect}
                            disabled={isDisconnecting}
                        >
                            {isDisconnecting ? <CircularProgress size={20} /> : 'Disconnect'}
                        </Button>
                    </>
                )}
            </Stack>
        </Box>
      </>
    );
}
