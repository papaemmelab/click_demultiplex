from os.path import join
from os import listdir
import os

from Bio import SeqIO
import click
import gzip


# Utils
def similarity_score(pattern, read, quality):
    if len(pattern) == len(read) == len(quality):
        return sum([
            abs((1 if read[index] == pattern[index] else 0) - quality[index]/40) * 100
            for index in range(len(pattern))
        ])
    raise Exception('Length of both reads do not match')


def hamming_distance(pattern1, pattern2):
    if len(pattern1) == len(pattern2):
        return sum([
            pattern1[index] != pattern2[index]
            for index in range(len(pattern1))
        ])
    raise Exception('Length of both reads do not match')


def find_array_positions(num, array):
    return [index for index, item in enumerate(array) if item == num][0]


def find_most_similar_paired(record1, record2, barcodes):
    if record1.id == record2.id:
        sequence1 = record1.seq[:6]
        sequence2 = record2.seq[:6]
        quality1 = record1.letter_annotations['phred_quality'][:6]
        quality2 = record2.letter_annotations['phred_quality'][:6]
        distance = [
            similarity_score(barcode, sequence1, quality1) +
            similarity_score(barcode, sequence2, quality2)
            for barcode in barcodes.values()
        ]
        matched_barcode = [
            barcode
            for barcode in barcodes.items()
        ][find_array_positions(min(distance), distance)]
        return matched_barcode
    raise Exception("R1 read sequence daoesn't match the R2 read sequence.")


def create_output_handle(output_dir, name, overwrite, direction):
    """ Validate that output dir and files exist."""
    if not os.path.isdir(output_dir):
        raise click.UsageError(
            f'Output directory {output_dir} doesn`t exist.'
        )

    file_path = join(output_dir, f'{name}_R{direction}.fastq')
    if os.path.isfile(file_path):
        if overwrite:
            os.remove(file_path)
        else:
            raise click.UsageError(message=(
                f'Output {file_path} file already exist. If you want to '
                'overwrite it, pass --overwrite as an option.'
            ))

    return open(file_path, 'a')

def get_files_handles(output_dir, barcodes, overwrite):
    """ Manage file handles to keep files open during demultiplexing."""
    return {
        cell: {
            'r1': create_output_handle(output_dir, cell, overwrite, 1),
            'r2': create_output_handle(output_dir, cell, overwrite, 2)
        }
        for cell in barcodes.keys()
    }

def close_file_handles(file_handles):
    for file_cell_handles in file_handles.values():
        file_cell_handles['r1'].close()
        file_cell_handles['r2'].close()


def get_barcodes(barcodes_path):
    """
    Creates a dictionary with the barcodes. Where the key is name that will
    be given to the output files, and the value is the barcode.
    If the text file have a 2nd column this value will be used as name, if not
    the same barcode will be the name.
    """
    barcodes_file = open(barcodes_path, 'r')
    barcodes_lines = [line.split() for line in barcodes_file.readlines()]
    return {
        (line[1] if len(line) == 2 else line[0]): line[0]
        for line in barcodes_lines
    }


# Main Function
def demultiplex(
        output_dir,
        r1_path,
        r2_path,
        barcodes_path,
        no_trim,
        overwrite):

    # Parse barcode dictionary
    barcodes = get_barcodes(barcodes_path)

    # Get handles for output files
    output_handles = get_files_handles(output_dir, barcodes, overwrite)

    # Collect some stats
    records_by_cell = {key: 0 for key in barcodes.keys()}

    # Select open method depending of the format
    open_r1 = gzip.open if r1_path.endswith('gz') else open
    open_r2 = gzip.open if r2_path.endswith('gz') else open

    # Open record one by one of each file, classify it and output to file.
    with open_r1(r1_path, 'rt') as fr1, open_r2(r2_path, 'rt') as fr2:

        filtered_seq_r1 = []
        filtered_seq_r2 = []

        records_r1_gen = SeqIO.parse(fr1, 'fastq')
        records_r2_gen = SeqIO.parse(fr2, 'fastq')

        for record_r1 in records_r1_gen:
            record_r2 = next(records_r2_gen)

            # Classify records according to barcode
            cell, barcode = find_most_similar_paired(record_r1, record_r2, barcodes)

            mismatches_r1 = hamming_distance(record_r1[:len(barcode)], barcode)
            mismatches_r2 = hamming_distance(record_r2[:len(barcode)], barcode)

            # Include only the trimmed sequences with 0 or 1 mismatch
            if mismatches_r1 <= 1 or mismatches_r2 <= 1:

                if no_trim:
                    filtered_seq_r1.append(record_r1)
                    filtered_seq_r2.append(record_r2)
                else:
                    filtered_seq_r1.append(record_r1[len(barcode):])
                    filtered_seq_r2.append(record_r2[len(barcode):])

            # Write to files
            SeqIO.write(filtered_seq_r1, output_handles[cell]['r1'], 'fastq')
            SeqIO.write(filtered_seq_r2, output_handles[cell]['r2'], 'fastq')

            # Store some stats
            records_by_cell[cell] += 1

    # Close Handles
    close_file_handles(output_handles)

    # Print Stats
    print(f'Finish Demultiplexing Files {r1_path} and {r2_path}')
    print('Stats of # of reads per barcode: ')
    print(records_by_cell)

