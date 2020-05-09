# water-parser

Parse (historical) alerts from water treatment companies.

The aim is to provide structured data that could be later used to make dashboards and visualisations.

To date, only [Odyssi](https://www.odyssi.fr/) from Martique is handled.
Contributions are welcomed.

## Usage
### Requirements
- python3.8

### Install

    mkvirtualenv water-parser

### Run
Download one (or all) page(s) from Odyssi.

    $ wget --no-check-certificate https://www.odyssi.fr/coupure/2077 -O /tmp/2077

Run the script

    $ water_parser --input_file /tmp/2077 --print
    period_from	period_to	reason
    2020-05-08	2020-05-08	casse

With the option `--output_dir`, a csv per period and a csv per day are written. Example:

    $ water_parser --input_file /tmp/2077 --output_dir /tmp
    $ ls /tmp/odyssi_*
    /tmp/odyssi_days.csv  /tmp/odyssi_periods.csv


## Visualisation

### Heatmap 

In the directory `html`, a [vega-lite](https://vega.github.io/vega-lite/) visualisation loads csv data (`day`format) and plot a `<month, day>` heatmap for the whole period (since 2013).

Heatmap can be exported to png or svg formats.
![pannes odyssi](https://dlo.center/img/odyssi-pannes.png)

One drawback is when multiple failure types occur one day, only one is kept.


## Todos

### Odyssi
- [ ] Extract locations from incident pages. Not so trivial as there are lots of errors, with different granularities and potentially ellipsis (lists ending with `...`)
- [ ] create a shortcut to retrieve (and parse) one page, the last `n` pages or the pages since a provided page `id` 

### SMeaux
- [ ] Identify if the same data can be extracted from the [smeaux](https://smeaux.fr/)

### Structure
- [ ] Generalize the parser to be able to handle easily more companies
