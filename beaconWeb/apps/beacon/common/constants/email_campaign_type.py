class EMAIL_CAMPAIGN_TYPE():
    TICKETS_LIVE = 'TL'
    MORE_EARLY_BIRD_LEFT = 'MB'
    LESS_EARLY_BIRD_LEFT = 'LB'
    REGULAR_LEFT = 'RL'
    FLASH_SALE = 'FS'
    DAY_OF_EMAIL = "DE"
    WEEK_OF_EMAIL = "WE"
    ENUM = (
            (TICKETS_LIVE, 'Tickets are now live'),
            (MORE_EARLY_BIRD_LEFT, 'More early bird tickets are left'),
            (LESS_EARLY_BIRD_LEFT, 'Less early bird tickets are left'),
            (REGULAR_LEFT, 'Regular tickets are left'),
            (FLASH_SALE, 'Flash sale for tickets'),
            (DAY_OF_EMAIL, 'Day of email'),
            (WEEK_OF_EMAIL, 'Week of email'),
        )
