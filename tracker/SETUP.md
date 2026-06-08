# Setup

## Email Alerts
Set these environment variables for email alerts:
  ALERT_EMAIL=your.gmail@gmail.com
  ALERT_PASSWORD=your-gmail-app-password  # generate at myaccount.google.com/apppasswords
  ALERT_TO=recipient@email.com  # optional, defaults to ALERT_EMAIL

Run with alerts enabled:
  python main.py --email
  python main.py --refresh 300 --email  # check every 5 minutes
