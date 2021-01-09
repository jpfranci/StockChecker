from model.website import Website

current_commands = f'''
**Current Commands:**
**!subscribe**: For help and detailed usage on available filters, message the bot !subscribe -h. Subscribe to be notified when an item goes in stock with given options. 
Basic usage !subscribe <url>

**!unsubscribe**: Unsubscribe from the notification list for an item. 
Usage: !unsubscribe <url>

**!get_subscribed**: Get all currently subscribed items for as well as the last n price histories for each item. 
Usage: !get_subscribed <last-n-prices> (defaults to 0)

**!unsubscribe_all**: Unsubscribe from all subscribed items

**!get_price_histories**: Get n last price histories for all listed items. 
Usage !get_price_histories <space separated list of item urls> <last-n-prices> (defaults to 5)
'''

subscribe_help_message = f'''
**About**: Subscribe to an item and be notified when a price dips below a threshold or if it goes in stock.

**Currently Supported Sites**: {", ".join([w.value for w in Website])}

**Example Usage**: 
1) Be notified when the item goes in stock at any price and it is sold by Amazon
!subscribe https://www.amazon.ca/gp/offer-listing/B06ZYZGWSV/ref=olp_twister_child?ie=UTF8&mv_color_name=2&mv_size_name=1

2) Be notified when the price goes under $69.69 and it is sold by Amazon
!subscribe https://www.amazon.ca/gp/offer-listing/B06ZYZGWSV/ref=olp_twister_child?ie=UTF8&mv_color_name=2&mv_size_name=1 -t 69.69

3) Be notified when the price goes under $69.69 and is in stock in sizes 00 X-Short or 00 for any seller, for any sizes that is more than one word please use quotations 
!subscribe https://www.ae.com/ca/en/p/women/curvy-jeans/curvy-highest-waist-jegging/ae-ne-x-t-level-curvy-highest-waist-jegging/3439_2356_038?menu=cat4840004 --threshold 69.69 --official-only no --size "00 X-Short" "00 Short"

**Usage**: !subscribe url [-t THRESHOLD] [-o OFFICIAL_ONLY] [-s SIZE] 

**Optional Arguments**:
-t THRESHOLD, --threshold THRESHOLD *Specify the price threshold to be notified. Defaults to any price.*
-o OFFICIAL_ONLY, --official-only OFFICIAL_ONLY *Only be notified when official sources go in stock (example sold by Amazon). Defaults to True*
-s SIZE, --size SIZE *For clothes in clothing sites, the clothing size that is being sought after.*
'''