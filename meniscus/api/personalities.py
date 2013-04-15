PERSONALITIES = [
    {
        'personality': 'correlation',
        'downstream': 'storage',
        'alternate': 'normalization'
    },
    {
        'personality': 'normalization',
        'downstream': 'storage',
        'alternate': ''
    },
    {
        'personality': 'storage',
        'downstream': '',
        'alternate': ''
    },
    {
        'personality': 'broadcaster',
        'downstream': '',
        'alternate': ''
    },
    {
        'personality': 'syslog',
        'downstream': 'storage',
        'alternate': 'normalization'
    }]

CORRELATION = 'correlation'
SYSLOG = 'syslog'
NORMALIZATION = 'normalization'
STORAGE = 'storage'
BROADCASTER = 'broadcaster'
