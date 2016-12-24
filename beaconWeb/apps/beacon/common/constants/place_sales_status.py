class PLACE_SALES_STATUS():
    CLOSED = 'CD'
    HADMEETING = 'HM'
    RESPONDED = 'RD'
    SAIDNO = 'SN'
    DONTCONTACT = 'DC'

    ENUM = (
            (CLOSED, 'Closed deal'),
            (HADMEETING, 'Had first meeting'),
            (RESPONDED, 'Responded'),
            (SAIDNO, 'Said no'),
            (DONTCONTACT, 'Do not contact')
    )