create table if not exists bom_movie_weekly (
  mojo_id text not null,
  year integer,
  week integer,
  studio text not null,
  weekly_gross integer,
  theater_count integer,
  PRIMARY KEY(mojo_id, year, week)
);

create table if not exists bom_movie_details (
  mojo_id text not null primary key,
  title text not null,
  distributor text not null,
  release_date date,
  genre text not null,
  runtime integer,
  mpaa_rate text not null,
  image_url text not null,
  budget integer
);

create table if not exists bom_weekly_movie_count (
  year integer,
  week integer,
  count integer,
  PRIMARY KEY(year, week)
);