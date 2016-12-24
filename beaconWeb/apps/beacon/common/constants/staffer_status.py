class STAFFER_STATUS():
    PRIMARY = 'PR'
    BACKUP = 'BK'
    DROPPED = 'DR'
    ENUM = (
            (PRIMARY, 'Primary'),
            (BACKUP, 'Backup'),
            (DROPPED, 'Dropped'),
        )