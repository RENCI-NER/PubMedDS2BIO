import argparse
from src.PubMedConvertor import stream as pubmed_stream

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Conversion tools')
    parser.add_argument('-i', '--input-format', help='input format')
    parser.add_argument('-o', '--output-format', help='output format')
    parser.add_argument('-f', '--file', help='input file')
    parser.add_argument('-d', '--output-file', help="output file")

    args = parser.parse_args()
    if args.input_format.lower() == 'pubmed_json':
        if args.output_format.lower() == 'iob':
            pubmed_stream(args.file, args.output_file, args.output_format)