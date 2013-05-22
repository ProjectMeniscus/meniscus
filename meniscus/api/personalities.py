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
    },
    {
        'personality': 'workercd d',
        'downstream': '',
        'alternate': ''
    },
    {
        'personality': 'coordinator',
        'downstream': '',
        'alternate': ''
    }]

CORRELATION = 'correlation'
SYSLOG = 'syslog'
NORMALIZATION = 'normalization'
STORAGE = 'storage'
BROADCASTER = 'broadcaster'
COORDINATOR = 'coordinator'
