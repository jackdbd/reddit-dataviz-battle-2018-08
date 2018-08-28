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


## Data

The entire TSA dataset is spread across multiple Excel files and PDF files. Download all files from [here](https://www.dhs.gov/tsa-claims-data) and put them in the `data` directory.

The script `make_db.py` gathers data from all the files (`.xls`, `.xlsx`, `.pdf`) and creates a SQLite database. You can run it with sane defaults with:

```sh
cd src
pipenv run python make_db.py
```

If you want to specify different parameters to read the PDF/Excel files, run:

```sh
pipenv run python make_db.py --help
```

For instance, it might be useful to run the script in debug mode to see what's going on with the PDF files.

This will drop the database and read only 2 pages in each PDF file, skipping all Excel files.

```sh
pipenv run python make_db.py -d --no_excel
```

## Usage

When your database `TSA.db` is ready, you can launch a Jupyter notebook and start exploring the data:

```sh
cd notebooks
pipenv run jupyter notebook
```
