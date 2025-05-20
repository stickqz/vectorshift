import { useState } from 'react';
import { Box, Button, Paper, Typography, Divider, Stack } from '@mui/material';
import axios from 'axios';
import { DataCard } from './DataCard';

const endpoints = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'HubSpot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    const [data, setData] = useState(null);
    const endpoint = endpoints[integrationType];

    const handleLoad = async () => {
        try {
            const fd = new FormData();
            fd.append('credentials', JSON.stringify(credentials));
            const res = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, fd);
            setData(res.data);
        } catch (e) {
            alert(e?.response?.data?.detail);
        }
    };

    return (
        <Box display="flex" justifyContent="center" alignItems="center" flexDirection="column" width="100%">
            <Box width="100%" maxWidth="700px">
                {data ? (
                    <Paper elevation={4} sx={{ p: 3, mt: 2, mb: 2 }}>
                        <Typography variant="h5" gutterBottom align="center" fontWeight={600}>
                            Loaded Data
                        </Typography>
                        <Divider sx={{ mb: 2 }} />
                        {Array.isArray(data) ? (
                            data.length > 0 ? data.map((item, idx) => <DataCard key={idx} item={item} />)
                            : <Typography color="text.secondary" align="center">No data found.</Typography>
                        ) : (
                            <DataCard item={data} />
                        )}
                    </Paper>
                ) : (
                    <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" sx={{ mt: 4, mb: 2 }}>
                        <img
                            src="/undraw_happy-music_na4p.svg"
                            alt="Ready to load data"
                            style={{ width: 180, marginBottom: 16, opacity: 0.8 }}
                        />
                        <Typography variant="h6" color="text.secondary" sx={{ fontWeight: 500 }}>
                            Ready to load your data!
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            Click the button below to fetch your integration data.
                        </Typography>
                    </Box>
                )}
                <Box display="flex" gap={2} sx={{ mt: 2 }} justifyContent="center">
                    <Button onClick={handleLoad} variant="contained">
                        Load Data
                    </Button>
                    {data && (
                        <Button onClick={() => setData(null)} variant="outlined">
                            Clear Data
                        </Button>
                    )}
                </Box>
            </Box>
        </Box>
    );
};
