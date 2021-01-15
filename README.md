# StockChecker
StockChecker is a Discord bot that allows users to track stock status of any item they want in several supported websites with a single command. To subscribe to 
tracking an item in a supported website, message the bot using `!subscribe <url>`.

The bot is highly customizable and supports notification settings by clothing size, who is selling it, and the price that you want to be notified at.
It parallelizes requests using asynchronous io, allowing for a large number of concurrent requests in each stock check cycle.
It supports retrieving stock statuses by selenium webdriver and also by directly requesting a website and retrieving relevant details using xpath.
