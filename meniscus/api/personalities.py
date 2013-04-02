PERSONALITIES = {
    'worker.correlation': {'downstream': 'worker.normalization'},
    'worker.normalization': {'downstream': 'worker.storage'},
    'worker.storage': {'downstream': 'worker.storage'}
}
