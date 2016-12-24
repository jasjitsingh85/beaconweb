class NOTIFICATION_TYPE():
    FRIEND_JOINED_PUSH = 'FJ'
    EVENT_RESERVED_PUSH = 'ER'
    NEW_HOTSPOTS_EMAIL = 'NH'
    FREE_DRINK_REMINDER_PUSH = 'FD'
    FRIEND_INVITED_PUSH = 'FI'
    WINBACK_EMAIL = "WE"
    IMAGE_ADDED = "IA"
    IMAGE_SEEN = "IS"
    BACKGROUND_NOTIFICATION = "BN"
    EVENT_FEEDBACK_EMAIL = "EF"
    USER_INTERVIEW_REQUEST = "IR"
    DIRECT_PUSH = "DP"
    ENUM = (
            (FRIEND_JOINED_PUSH, 'Friend Joined'),
            (NEW_HOTSPOTS_EMAIL, 'New Hotspots Email'),
            (FREE_DRINK_REMINDER_PUSH, 'Free Drink Reminder Push'),
            (FRIEND_INVITED_PUSH, 'Friend Invited to Hotspot'),
            (WINBACK_EMAIL, "Free Drink Winback Email"),
            (IMAGE_ADDED, "Image Added"),
            (IMAGE_SEEN, "Image Seen"),
            (EVENT_RESERVED_PUSH, "Event Reserved Push"),
            (BACKGROUND_NOTIFICATION, "Background Notification"),
            (EVENT_FEEDBACK_EMAIL, "Event Feedback Email"),
            (USER_INTERVIEW_REQUEST, "User Interview Request"),
            (DIRECT_PUSH, "Direct Push")
        )