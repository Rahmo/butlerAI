DEFAULT_RULES = [
    # marketing / promos
    'category:promotions older_than:7d',
    'subject:(newsletter OR unsubscribe OR promotion OR deal OR offer) older_than:14d',

    # social
    'category:social older_than:7d',
    'from:(facebookmail.com OR twitter.com OR linkedin.com OR instagram.com OR tiktok.com) older_than:14d',

    # delivery / shopping
    'subject:(delivered OR shipment OR tracking OR order confirmation OR order update) older_than:21d',
    'from:(noreply@amazon.com OR noreply@ebay.com OR walmart.com) older_than:21d',

    # login / auth codes
    'subject:("verification code" OR "security alert" OR "sign-in attempt") older_than:14d',

    # newsletters (many don’t use Gmail categories)
    'list:(*) older_than:21d',

    # old auto notifications
    'subject:(notification OR alert OR digest OR summary) older_than:30d',

    # large old emails (optional, uncomment if you want)
    # 'larger:10M older_than:90d',
]
