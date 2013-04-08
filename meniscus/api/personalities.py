PERSONALITIES = [
    {
        'personality': 'worker.correlation',
        'downstream': 'worker.storage',
        'alternate': 'worker.normalization'
    },
    {
        'personality': 'worker.normalization',
        'downstream': 'worker.storage',
        'alternate': ''
    },
    {
        'personality': 'worker.storage',
        'downstream': '',
        'alternate': ''
    }]