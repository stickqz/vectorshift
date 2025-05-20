import { Paper, Typography, Divider, Stack, Box } from '@mui/material';

export function DataCard({ item }) {
    // Define field categories
    const primaryFields = ['name', 'from', 'title', 'subject'];
    const metaFields = ['status', 'date', 'time', 'id'];
    const contentFields = ['message', 'content', 'description', 'note'];

    // Extract fields
    const getValue = (obj, key) => obj[key] ?? null;

    const vals = Object.entries(item).filter(([_, v]) => v != null);
    const primary = primaryFields.map(f => getValue(item, f)).find(v => v);
    const meta = metaFields.map(f => getValue(item, f)).filter(v => v);

    const content = contentFields.map(f => getValue(item, f)).find(v => v);
    const shownFields = [...primaryFields, ...metaFields, ...contentFields];
    const otherFields = vals.filter(([k]) => !shownFields.includes(k));

    return (
        <Paper elevation={3} sx={{ p: 3, borderRadius: 3, background: '#f9f9fb', mb: 2 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                <Box>
                    {primary && (
                        <Typography variant="h6" fontWeight="bold" sx={{ fontSize: '1.2rem' }}>
                            {primary}
                        </Typography>
                    )}
                </Box>
                <Stack spacing={0.5} alignItems="flex-end">
                    {meta.map((v, i) => (
                        <Typography key={i} variant="subtitle2" color="text.secondary" sx={{ fontSize: '0.95rem' }}>
                            {v}
                        </Typography>
                    ))}
                </Stack>
            </Stack>
            {content && (
                <>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {content}
                    </Typography>
                </>
            )}
            {otherFields.length > 0 && (
                <>
                    <Divider sx={{ my: 1 }} />
                    <Stack spacing={0.5}>
                        {otherFields.map(([key, value]) => (
                            <Stack key={key} direction="row" alignItems="center" spacing={1}>
                                <Typography variant="subtitle2" color="text.secondary" sx={{ minWidth: 90 }}>
                                    {key.charAt(0).toUpperCase() + key.slice(1)}:
                                </Typography>
                                <Typography variant="body2">
                                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </Typography>
                            </Stack>
                        ))}
                    </Stack>
                </>
            )}
        </Paper>
    );
} 