"""=click_demultiplex cli tests."""

from os.path import abspath
from os.path import dirname
from os.path import join
from glob import glob
import subprocess

from Bio import SeqIO
from click.testing import CliRunner
import click
import pandas as pd
import pytest

from click_demultiplex import cli
from click_demultiplex import commands


ROOT = abspath(dirname(__file__))
TEST_R1 = join(ROOT, 'data', 'test_R1.fastq')
TEST_R2 = join(ROOT, 'data', 'test_R2.fastq')
TEST_BARCODES = join(ROOT, 'data', 'test_barcodes.txt')


def test_cli(tmpdir):
    params = [
        "--r1", TEST_R1,
        "--r2", TEST_R2,
        "--outdir", tmpdir.strpath,
        "--barcodes", TEST_BARCODES,
    ]
    result = CliRunner().invoke(cli.main, params)
    assert result.exit_code == 0


def test_defaults(tmpdir):
    params = {
        'barcodes_path': TEST_BARCODES,
        'max_mismatches': 1,
        'not_trim': False,
        'output_dir': tmpdir.strpath,
        'overwrite': False,
        'prefix': '',
        'r1_path': TEST_R1,
        'r2_path': TEST_R2,
    }
    commands.demultiplex(*params.values())
    assert_output(**params)


def test_trim(tmpdir):
    params = {
        'barcodes_path': TEST_BARCODES,
        'max_mismatches': 1,
        'not_trim': True,
        'output_dir': tmpdir.strpath,
        'overwrite': True,
        'prefix': '',
        'r1_path': TEST_R1,
        'r2_path': TEST_R2,
    }
    commands.demultiplex(*params.values())
    assert_output(**params)


def test_prefix(tmpdir):
    params = {
        'barcodes_path': TEST_BARCODES,
        'max_mismatches': 1,
        'not_trim': True,
        'output_dir': tmpdir.strpath,
        'overwrite': True,
        'prefix': 'my_weird_prefix',
        'r1_path': TEST_R1,
        'r2_path': TEST_R2,
    }
    commands.demultiplex(*params.values())
    assert_output(**params)


def test_max_mismatches(tmpdir):
    params = {
        'barcodes_path': TEST_BARCODES,
        'max_mismatches': 0,
        'not_trim': True,
        'output_dir': tmpdir.strpath,
        'overwrite': True,
        'prefix': 'my_weird_prefix',
        'r1_path': TEST_R1,
        'r2_path': TEST_R2,
    }
    commands.demultiplex(*params.values())

    params['max_mismatches'] = 1
    commands.demultiplex(*params.values())
    assert_output(**params)

    params['max_mismatches'] = 2
    commands.demultiplex(*params.values())
    assert_output(**params)

    params['max_mismatches'] = 3
    commands.demultiplex(*params.values())
    assert_output(**params)


def test_overwrite(tmpdir):
    params = {
        'barcodes_path': TEST_BARCODES,
        'max_mismatches': 1,
        'not_trim': False,
        'output_dir': tmpdir.strpath,
        'overwrite': True,
        'prefix': '',
        'r1_path': TEST_R1,
        'r2_path': TEST_R2,
    }
    commands.demultiplex(*params.values())
    commands.demultiplex(*params.values())

    params['overwrite'] = False
    with pytest.raises(click.UsageError) as excinfo:
        commands.demultiplex(*params.values())
    assert 'pass --overwrite as an option' in excinfo.value.message


def assert_output(
        r1_path,
        r2_path,
        barcodes_path,
        output_dir,
        overwrite,
        prefix,
        not_trim,
        max_mismatches):

    # Parse r1 and r2
    multiplexed_r1 = SeqIO.parse(r1_path, 'fastq')
    original_sequence_length = len(next(multiplexed_r1))

    # Parse barcodes
    barcodes = commands.get_barcodes(barcodes_path)

    # Output files
    stats_file = join(output_dir, f'{prefix}result_stats.txt')
    output_files = glob(join(output_dir, '*.fastq'))

    # Parse Result stats file
    stats = pd.read_csv(
        stats_file,
        sep='\t',
        skiprows=1,
        skipfooter=1,
        engine='python',
        index_col=False
    )
    stats_dict = stats.set_index('Name').to_dict('index')

    # Assert number of output files
    assert len(barcodes.keys()) == len(stats)
    assert len(barcodes.keys()) * 2 == len(output_files)

    for name, barcode in barcodes.items():
        r1_filename = f'{prefix}{name}_R1.fastq'
        r2_filename = f'{prefix}{name}_R2.fastq'

        r1_path = join(output_dir, r1_filename)
        r2_path = join(output_dir, r2_filename)

        with open(r1_path, 'rt') as fr1, open(r2_path, 'rt') as fr2:
            records_r1 = list(SeqIO.parse(fr1, 'fastq'))
            records_r2 = list(SeqIO.parse(fr2, 'fastq'))

            assert len(records_r1) == len(records_r2)
            assert stats_dict[name]['Barcode'] == barcode
            assert stats_dict[name]['Count'] == len(records_r1)
            assert r1_filename in stats_dict[name]['Output R1 file']
            assert r2_filename in stats_dict[name]['Output R2 file']
            assert_quantity_of_filtered_sequences(stats_file, max_mismatches)

            for index in range(len(records_r1)):
                expected_sequence_length = original_sequence_length - (
                    0 if not_trim else len(barcode)
                )
                assert records_r1[index].id == records_r2[index].id
                assert len(records_r1[index].seq) == expected_sequence_length
                assert len(records_r2[index].seq) == expected_sequence_length


def assert_quantity_of_filtered_sequences(stats_file, max_mismatches):
    result_line = subprocess.check_output(['tail', '-1', stats_file])
    results_filtered_count = int(result_line.split()[3])
    expected_filtered_count = [35, 36, 60, 158, 250, 250, 250]
    assert expected_filtered_count[max_mismatches] == results_filtered_count
