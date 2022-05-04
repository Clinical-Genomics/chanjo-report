![Example report (eng)](artwork/screenshot.png)

# Chanjo Report
Automatically generate basic coverage reports from Chanjo SQL databases. This plugin installs as a subcommand ("report") to the Chanjo command line interface.

## Usage
Visualize a coverage report for one ore more samples using the following command:

```bash
$ chanjo --database mysql+pymysql://<db-user>:<db-password>@localhost:3306/<db-name> report --sample sample1 --sample sample2 --sample sample3
```

## Features

### Supported output formats
Chanjo Reports multiple output formats:

  - tabular: easily parsable and pipeable
  - PDF: easily distributable (for humans)
  - HTML: easily deliverable on the web

### Supported languages (translations)
The coverage report (HTML/PDF) can be render is the following languages:

  - English
  - Swedish


## Motivation
We are using the output from Chanjo at Clincal Genomics to report success of sequencing across the exome based on coverage. Our customers, clinicians mostly, are specifically interested in knowing to what degree their genes of interest are covered by sequencing along with some intuitive overall coverage metrics. They want the output in PDF format to file it in their system.

As a side effect of finding it easiest to convert HTML to PDF, Chanjo Report has a built in Flask server that can be used to render reports dynamically and even be plugged into other Flask servers as a Blueprint.


### Installation

The latest version of Chanjo-report can be installed by cloning and installing the repository from Clinical Genomics github:

```bash
$ git clone https://github.com/Clinical-Genomics/chanjo-report.git
$ cd chanjo-report
$ pip install --editable .
```


## License
MIT. See the [LICENSE](LICENSE) file for more details.


## Contributing
Anyone can help make this project better - read [CONTRIBUTING](CONTRIBUTING.md) to get started!
