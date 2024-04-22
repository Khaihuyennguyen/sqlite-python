[![progress-banner](http://www.codebind.com/wp-content/uploads/2016/09/SQLite-623x381.jpg)](https://www.sqlite.org/fileformat.html#b_tree_pages)

# Engine my Own SQLite 
This project is to understand how SQL queries work under the hood in database such as SQLite.


In this challenge, I'll build a barebones SQLite implementation that supports
basic SQL queries like `SELECT`, `WHERE`. Along the way I will demonstrate and recreate some basic command based on 
offical document [SQLite's file format](https://www.sqlite.org/fileformat.html), how indexed data [stored in B-trees](https://jvns.ca/blog/2014/10/02/how-does-sqlite-work-part-2-btrees/) and more.



## Getting started

The entry point for my SQLite implementation is in `app/main.py`.


### Prerequisites

Note: This section is for environemnt set up and beyond.

1. Ensure you have `python (3.8+)` installed locally

# Sample Databases

To make it easy to test queries locally, I have added a sample database in the
root of this repository: `sample.db`.

This contains two tables: `apples` & `oranges`. You can use this to test your
implementation for the first 6 simple queries.

You can explore this database by running queries against it like this:

```
$ python3  app/main.py sample.db "select color, name from apples"
Light Green|Granny Smith
Red|Fuji
Blush Red|Honeycrisp
Yellow|Golden Delicious
```

There are some commands that you can try:

1. `python app/main.py sample.db .dbinfo`
1. `python app/main.py sample.db .tables`
1. `python app/main.py sample.db "SELECT COUNT(*) FROM apples"`
1. `python app/main.py sample.db "SELECT name FROM apples"`
1. `python app/main.py sample.db "SELECT name, color FROM apples"`
2. `python app/main.py sample.db "SELECT name, color FROM apples WHERE color = 'Yellow'"`


# Future development:

#### Medium blog (Apr 24)






