"""click_demultiplex main command."""

from os.path import join
import os
import gzip
import subprocess

from Bio import SeqIO
import click


# Utils for classifying Sequences
def hamming_distance(pattern1, pattern2):
    """Return the hamming distance between 2 patterns."""
    if len(pattern1) == len(pattern2):
        return sum([
            pattern1[index] != pattern2[index]
            for index in range(len(pattern1))
        ])
    raise Exception('Length of both reads do not match')


def find_best_barcode(record, barcodes):
    """Return the best hamming distance barcode."""
    distance = [
        hamming_distance(barcode, record.seq[:len(barcode)])
        for barcode in barcodes.values()
    ]
    min_distance = min(distance)
    matched_barcode = [
        barcode
        for barcode in barcodes.items()
    ][distance.index(min(distance))]
    return matched_barcode + (min_distance,)


def find_best_match(record1, record2, barcodes, max_mismatches):
    """Return the best match barcode between R1 and R2."""
    name1, barcode1, distance1 = find_best_barcode(record1, barcodes)
    name2, barcode2, distance2 = find_best_barcode(record2, barcodes)

    if distance1 <= distance2 and distance1 <= max_mismatches:
        return name1, barcode1
    elif distance2 <= distance1 and distance2 <= max_mismatches:
        return name2, barcode2
    return None, None


# Utils to manage files handles
def create_output_handle(output_dir, name, overwrite, prefix, direction):
    """Validate that output dir and files exist."""
    if not os.path.isdir(output_dir):
        raise click.UsageError(
            f'Output directory {output_dir} doesn`t exist.'
        )

    file_path = join(output_dir, f'{prefix}{name}_R{direction}.fastq')
    if os.path.isfile(file_path):
        if overwrite:
            os.remove(file_path)
        else:
            raise click.UsageError(message=(
                f'Output {file_path} file already exist. If you want to '
                'overwrite it, pass --overwrite as an option.'
            ))

    return open(file_path, 'a')


def get_files_handles(output_dir, barcodes, overwrite, prefix):
    """Manage file handles to keep files open during demultiplexing."""
    return {
        cell: {
            'r1': create_output_handle(output_dir, cell, overwrite, prefix, 1),
            'r2': create_output_handle(output_dir, cell, overwrite, prefix, 2)
        }
        for cell in barcodes.keys()
    }

def close_file_handles(file_handles):
    """Close every opened file."""
    for file_cell_handles in file_handles.values():
        file_cell_handles['r1'].close()
        file_cell_handles['r2'].close()


# Util to parse barcodes
def get_barcodes(barcodes_path):
    """
    Create a dictionary with the barcodes.

    Where the key is name that will be given to the output files, and
    the value is the barcode. If the text file have a 2nd column this
    value will be used as name, if not the same barcode will be the name.
    """
    barcodes_file = open(barcodes_path, 'r')
    barcodes_lines = [line.split() for line in barcodes_file.readlines()]
    return {
        (line[1] if len(line) == 2 else line[0]): line[0]
        for line in barcodes_lines
    }


# Utils to create output files
def create_output_stats(
        output_dir,
        stats,
        barcodes,
        output_handles,
        initial_count,
        prefix):
    """Print stats of results."""
    output_stats_path = join(output_dir, f'{prefix}result_stats.txt')

    with open(output_stats_path, 'w') as output_stats_file:
        output_stats_file.write('Stats of # of reads per barcode:\n\n')
        output_stats_file.write("{}\t{}\t{}\t{}\t{}\n".format(
            'Barcode', 'Name', 'Count', 'Output R1 file', 'Output R2 file'
        ))
        for name, count in stats.items():
            output_stats_file.write("{}\t{}\t{}\t{}\t{}\n".format(
                barcodes[name],
                name,
                count,
                output_handles[name]['r1'].name,
                output_handles[name]['r2'].name,
            ))
        final_count = sum(stats.values())
        output_stats_file.write(
            f'\nA total of {final_count} from {initial_count} '
            f'reads were demultiplexed.\n'
        )
    subprocess.check_call(["cat", output_stats_path])


# Main Function
def demultiplex(
        barcodes_path,
        max_mismatches,
        no_trim,
        output_dir,
        overwrite,
        prefix,
        r1_path,
        r2_path):
    """Demultiplex one file into several according the barcodes file."""
    # Parse barcode dictionary
    barcodes = get_barcodes(barcodes_path)

    # Get handles for output files
    output_handles = get_files_handles(output_dir, barcodes, overwrite, prefix)

    # Collect some stats
    records_by_cell = {key: 0 for key in barcodes.keys()}

    # Select open method depending of the format of the files
    open_r1 = gzip.open if r1_path.endswith('gz') else open
    open_r2 = gzip.open if r2_path.endswith('gz') else open

    # Open record one by one of each file, classify it and output to file.
    with open_r1(r1_path, 'rt') as fr1, open_r2(r2_path, 'rt') as fr2:

        # Get generators for both files
        records_r1_gen = SeqIO.parse(fr1, 'fastq')
        records_r2_gen = SeqIO.parse(fr2, 'fastq')

        label = f'Started demultiplexing files {r1_path} and {r2_path}'
        with click.progressbar(records_r1_gen, label=label) as bar:

            initial_count = 0

            for record_r1 in bar:
                record_r2 = next(records_r2_gen)

                # Store some stats
                initial_count += 1

                cell, barcode = find_best_match(
                    record_r1,
                    record_r2,
                    barcodes,
                    max_mismatches
                )

                if cell and barcode:

                    # Trim unless flag is passed
                    if not no_trim:
                        record_r1 = record_r1[len(barcode):]
                        record_r2 = record_r2[len(barcode):]

                    # Collect stats of demultiplexed ones
                    records_by_cell[cell] += 1

                    # Write to files
                    SeqIO.write(record_r1, output_handles[cell]['r1'], 'fastq')
                    SeqIO.write(record_r2, output_handles[cell]['r2'], 'fastq')

    # Close Handles
    close_file_handles(output_handles)

    # Print Stats
    create_output_stats(
        output_dir,
        records_by_cell,
        barcodes,
        output_handles,
        initial_count,
        prefix
    )
