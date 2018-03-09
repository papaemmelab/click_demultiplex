"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?
You might be tempted to import things from __main__ later, but that will
cause problems, the code will get executed twice:

    - When you run `python -m click_demultiplex` python will execute
      `__main__.py` as a script. That means there won't be any
      `click_demultiplex.__main__` in `sys.modules`.

    - When you import __main__ it will get executed again (as a module) because
      there's no `click_demultiplex.__main__` in `sys.modules`.

Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

import click

from click_demultiplex import __version__
from click_demultiplex import commands


@click.command()
@click.option(
    "--outdir",
    show_default=True,
    required=True,
    help="Path to output directory.",
    default=None)
@click.option(
    "--r1",
    required=True,
    type=click.Path(exists=True),
    help="Path to R1 fastq file. Reads in forward orientation")
@click.option(
    "--r2",
    required=True,
    type=click.Path(exists=True),
    help="Path to R2 fatsq file. Reads in reverse-complement orientation")
@click.option(
    "--barcodes",
    required=True,
    type=click.Path(exists=True),
    help="A text file with the barcodes in each line.")
@click.option(
    "--prefix",
    default="",
    help="String to add to output files.")
@click.option(
    "--no-trim",
    default=False,
    is_flag=True,
    help="Flag to avoid trimming the barcodes in each read.")
@click.option(
    "--overwrite",
    default=False,
    is_flag=True,
    help="Flag to overwrite the output files if they already exist.")
@click.option(
    "--max-mismatches",
    default=1,
    show_default=True,
    help="Maximum number of mismatches allowed in the barcode to demultiplex.")
@click.version_option(__version__)
def main(outdir, r1, r2, barcodes, no_trim, overwrite, prefix, max_mismatches):
    r"""
    Demultiplex a paired-end fastq file into several based on unique barcodes.

    The barcodes are sequences attached at the beginning of each read.
    By default, it trimms the barcodes off the demultiplexed reads,
    unless --no-trim is passed.

    The barcodes text file should be formatted to have 1 column with
    the barcodes, and an optional additional column to assign names to
    the demultiplexed result files.  the following structure:

        \b
        ATTCGT       A1
        ATATTC       A2
        TCGGAC       B1
        TCGAGG       B2
    """
    prefix = prefix if prefix.endswith('_') else f'{prefix}_'

    commands.demultiplex(
        barcodes_path=barcodes,
        max_mismatches=max_mismatches,
        no_trim=no_trim,
        prefix=prefix,
        output_dir=outdir,
        overwrite=overwrite,
        r1_path=r1,
        r2_path=r2,
    )

if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
