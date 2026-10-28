# RateNow v2 (god mode) - setup

## Ek baar ka setup (~15 minute)
1. GitHub par naya **public** repo banao: `ratenow`
2. Is zip ki saari files upload karo (`.github` folder samet)
3. `config.json` mein `YOURUSERNAME` apne GitHub username se badlo, email likho
4. Repo > **Settings > Pages** > Source: **GitHub Actions**
5. Repo > **Actions** > "daily-update" > **Run workflow** (pehli dafa 45 din ki asli history bhi khud utha leta hai)
6. 3-5 minute baad site live: `https://USERNAME.github.io/ratenow`
7. Google Search Console mein site add karo aur `sitemap.xml` submit karo

## Baad mein (optional, jab chaho)
- **AdSense:** traffic aane par apply karo, phir `config.json` mein `adsense_client` aur `adsense_slot` bharo
- **Analytics:** `ga_id` mein Google Analytics ID daalo (traffic dekhne ke liye)
- **Telegram channel (free audience, khud post hoti hai):** @BotFather se bot banao, channel mein bot ko admin banao, repo
  Settings > Secrets > Actions mein `TELEGRAM_BOT_TOKEN` aur `TELEGRAM_CHAT_ID` daalo, aur channel ka link `telegram_channel_url` mein
- **Affiliate (remittance wala paisa):** `affiliate_url` mein apna link daalo, send-money aur har pair page par box aa jayega

## Roz khud kya hota hai
Naye rates, history, charts, insights, 1900+ pages, sitemap, RSS, API, Bing/IndexNow ping aur Telegram post. Tumhein kuch nahi karna.
