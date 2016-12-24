class DISPLAY_LOCATIONS():
    INVITE_NEW_USERS = 'IU'
    FRIEND_ALREADY_INVITED_DIALOG = 'FI'
    ZERO_HOTSPOTS_MESSAGE = 'ZH'
    SET_HOTSPOT_PLACEHOLDER = 'SP'
    SET_HOTSPOT_NO_CONTENT_DIALOG = "SN"


    ENUM = (
            (INVITE_NEW_USERS, 'Text for inviting new users to App'),
            (FRIEND_ALREADY_INVITED_DIALOG, 'Dialog for if friend has already been invited'),
            (ZERO_HOTSPOTS_MESSAGE, 'Message for when there are no Hotspots'),
            (SET_HOTSPOT_PLACEHOLDER, 'Placeholder text for Hotspot description'),
            (SET_HOTSPOT_NO_CONTENT_DIALOG, 'Dialog content if user neglects to add description')
    )