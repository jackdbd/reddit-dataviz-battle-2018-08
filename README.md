# Reddit DataViz Battle August 2018

Code for the Reddit dataisbeautiful [DataViz Battle for the Month of August 2018](https://www.reddit.com/r/dataisbeautiful/comments/950j3n/battle_dataviz_battle_for_the_month_of_august/)

Analysis and visual exploration of [TSA Claims Data](https://www.dhs.gov/tsa-claims-data).


## Installation

This repository uses pipenv. If you need to install it you can follow the [documentation](https://pipenv.readthedocs.io/en/latest/).

Create a pyhon 3.6 environment and install all the dependencies:

```sh
git clone git@github.com:jackdbd/reddit-dataviz-battle-2018-08.git
cd reddit-dataviz-battle-2018-08
pipenv --python python3.6
pipenv install
```

The entire TSA dataset is spread across multiple Excel files and PDF files.

The script `make_db.py` gathers data from all the files (`.xls`, `.xlsx`, `.pdf`) and creates a SQLite database. Launch it with:

```sh
pipenv run make_db.py
```


## Usage

Whan your database `tsa.db` is ready, you can launch a Jupyter notebook and start exploring the data:

```sh
pipenv run jupyter notebook
```
