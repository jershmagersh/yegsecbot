# YEGSECBOT

## Database Schema

### Tables & Columns

* Users
    * slack_id (pk)
* Years
    * year_id (pk)
* Months
    * month_id (pk)
* Day
    * day_id (pk)
* Talks
    * talk_id (pk)
    * title
    * summary
    * year_id (fk)
    * month_id (fk)
* Meetup
    * meetup_id (pk)
    * year_id (fk)
    * month_id (fk)
    * day_id (fk)
    * att_total
