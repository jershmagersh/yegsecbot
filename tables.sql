CREATE TABLE users (
 user_id integer text 
);

CREATE TABLE years (
 year_id integer PRIMARY KEY
);

CREATE TABLE months (
 month_id integer PRIMARY KEY
);

CREATE TABLE days (
 day_id integer PRIMARY KEY
);

CREATE TABLE confirmations (
 user_id integer NOT NULL,
 meetup_id integer NOT NULL,
 pizza_pref integer NOT NULL,
 FOREIGN KEY (user_id) REFERENCES users(user_id),
 FOREIGN KEY (meetup_id) REFERENCES meetups(meetup_id)
);

CREATE TABLE talks (
 talk_id integer PRIMARY KEY,
 title text NOT NULL,
 summary text NOT NULL,
 month_id integer NOT NULL,
 day_id integer NOT NULL,
 year_id integer NOT NULL,
 FOREIGN KEY (year_id) REFERENCES years(year_id),
 FOREIGN KEY (day_id) REFERENCES days(day_id),
 FOREIGN KEY (month_id) REFERENCES month(month_id)
);

CREATE TABLE meetups (
 meetup_id integer PRIMARY KEY,
 month_id integer NOT NULL,
 day_id integer NOT NULL,
 year_id integer NOT NULL,
 talk_id integer NOT NULL,
 location text NOT NULL,
 pizza_count_total integer NOT NULL,
 pizza_count_veg integer NOT NULL,
 pizza_count_other integer NOT NULL,
 FOREIGN KEY (year_id) REFERENCES years(year_id),
 FOREIGN KEY (day_id) REFERENCES days(day_id),
 FOREIGN KEY (month_id) REFERENCES month(month_id),
 FOREIGN KEY (talk_id) REFERENCES talks(talk_id)
);
