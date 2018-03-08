# click_demultiplex

[![pypi badge][pypi_badge]][pypi_base]
[![travis badge][travis_badge]][travis_base]
[![codecov badge][codecov_badge]][codecov_base]

Demultiplex a paired-end fastq file into several fastq files,
based on unique barcodes.
The barcodes are sequences attached at the beginning of each read.
By default, it trimms the barcodes off the demultiplexed reads,
unless --no-trim is passed.

The barcodes text file should be formatted to have 1 column with
the barcodes, and an optional additional column to asign names to
the demultiplexed result files.  the following structure:

    ATTCGT       A1
    ATATTC       A2
    TCGGAC       B1
    TCGAGG       B2

## 📦 &nbsp; **Installation**

    pip install click_demultiplex

## 🍉 &nbsp; **Usage**

        click_demultiplex --help

        click_demultiplex \
            --r1 test/data/test_R1.fastq \
            --r2 test/data/test_R2.fastq \
            --barcodes test/data/test_barcodes.txt \
            --outdir my_output_dir \
            --prefix plate_0008
            --no-trim

## 🐳 &nbsp; **Containers Support**

* docker usage

        docker run \
            --volume /shared_fs:/shared_fs \
            --interactive \
            --tty \
            click_demultiplex-image \
                --r1 /code/test/data/test_R1.fastq \
                --r2 /code/test/data/test_R2.fastq \
                --barcodes /code/test/data/test_barcodes.txt \
                --outdir /code/my_output_dir \

* singularity usage

        singularity run \
            --workdir /shared_fs/tmp \
            --bind /shared_fs:/shared_fs \
            click_demultiplex-singularity-image-path \
                --r1 /code/test/data/test_R1.fastq \
                --r2 /code/test/data/test_R2.fastq \
                --barcodes /code/test/data/test_barcodes.txt \
                --outdir /code/my_output_dir \


## Contributing

Contributions are welcome, and they are greatly appreciated, check our [contributing guidelines](.github/CONTRIBUTING.md)!

## Credits

This package was created using [Cookiecutter] and the
[leukgen/cookiecutter-toil] project template.

<!-- References -->
[singularity]: http://singularity.lbl.gov/
[docker2singularity]: https://github.com/singularityware/docker2singularity
[cookiecutter]: https://github.com/audreyr/cookiecutter
[leukgen/cookiecutter-toil]: https://github.com/leukgen/cookiecutter-toil

<!-- Badges -->
[codecov_badge]: https://codecov.io/gh/juanesarango/click_demultiplex/branch/master/graph/badge.svg
[codecov_base]: https://codecov.io/gh/juanesarango/click_demultiplex
[pypi_badge]: https://img.shields.io/pypi/v/click_demultiplex.svg
[pypi_base]: https://pypi.python.org/pypi/click_demultiplex
[travis_badge]: https://img.shields.io/travis/juanesarango/click_demultiplex.svg
[travis_base]: https://travis-ci.org/juanesarango/click_demultiplex
