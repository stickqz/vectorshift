import { useState } from 'react';
import { Box, Autocomplete, TextField, Typography, Paper } from '@mui/material';

import { AirtableIntegration } from './integrations/airtable';
import { NotionIntegration } from './integrations/notion';
import { HubSpotIntegration } from './integrations/hubspot';
import { DataForm } from './DataForm';


const integrations = {
    'Notion': NotionIntegration,
    'Airtable': AirtableIntegration,
    'HubSpot': HubSpotIntegration,
};

export const IntegrationForm = () => {
    const [params, setParams] = useState({});
    const [user, setUser] = useState('JohnDoe');
    const [org, setOrg] = useState('TestOrg');
    const [selectedType, setSelectedType] = useState(null);
    const SelectedIntegration = integrations[selectedType];

    return (
        <Box
            display="flex"
            width="100vw"
            height="95vh"
            sx={{ background: 'linear-gradient(90deg, #f6f7fa 60%, #e9ecef 100%)', minHeight: 0 }}
        >
            {/* Left: Form */}
            <Box
                display="flex"
                flexDirection="column"
                alignItems="center"
                justifyContent="center"
                sx={{
                    width: 520,
                    minWidth: 420,
                    maxWidth: 580,
                    height: '100vh',
                    boxShadow: '2px 0 16px 0 rgba(0,0,0,0.04)',
                    bgcolor: '#fff',
                    zIndex: 2,
                    position: 'relative',
                }}
            >
                <Typography
                    variant="h3"
                    sx={{
                        textAlign: 'center',
                        fontWeight: 700,
                        letterSpacing: 1,
                        mb: 3,
                        color: '#1a2a3a',
                    }}
                >
                    <span style={{ color: '#2e7d32' }}>Vector</span>Shift Integrations
                </Typography>

                <Paper elevation={2} sx={{ p: 4, borderRadius: 3, width: '100%', maxWidth: 360, bgcolor: '#fafbfc' }}>
                    <Box display='flex' flexDirection='column' gap={2}>
                        <TextField
                            label="User"
                            value={user}
                            onChange={(e) => setUser(e.target.value)}
                            variant="outlined"
                            size="medium"
                        />
                        <TextField
                            label="Organization"
                            value={org}
                            onChange={(e) => setOrg(e.target.value)}
                            variant="outlined"
                            size="medium"
                        />
                        {!params?.credentials && (
                            <Autocomplete
                                id="integration-type"
                                options={Object.keys(integrations)}
                                sx={{ width: '100%' }}
                                renderInput={(params) => <TextField {...params} label="Integration Type" />}
                                onChange={(e, value) => setSelectedType(value)}
                            />
                        )}
                        {selectedType && (
                            <Box mt={2}>
                                <SelectedIntegration
                                    user={user}
                                    org={org}
                                    integrationParams={params}
                                    setIntegrationParams={setParams}
                                />
                            </Box>
                        )}
                    </Box>
                </Paper>
            </Box>

            {/* Right: Data */}
            <Box
                display="flex"
                flexDirection="column"
                alignItems="center"
                sx={{
                    flexGrow: 1,
                    height: '100%',
                    minHeight: 0,
                    overflowY: 'auto',
                    p: 3,
                    bgcolor: 'transparent',
                }}
            >
                {!params?.credentials ? (
                    <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" sx={{ mt: 8 }}>
                        <img
                            src="/undraw_happy-music_na4p.svg"
                            alt="Nothing to show"
                            style={{ width: 220, marginBottom: 24, opacity: 0.8 }}
                        />
                        <Typography variant="h5" color="text.secondary" sx={{ fontWeight: 500 }}>
                            Nothing to show
                        </Typography>

                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            Please select an integration and connect to see your data here.
                        </Typography>
                    </Box>
                ) : (
                    <Box sx={{ width: '100%', maxWidth: 900, marginLeft: '20%' }}>
                        <DataForm integrationType={params?.type} credentials={params?.credentials} />
                    </Box>
                )}
            </Box>
        </Box>
    );
}
