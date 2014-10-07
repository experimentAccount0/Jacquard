from __future__ import print_function
import collections
import glob
import os
import shutil

from variant_callers import variant_caller_factory
import utils
from utils import JQException, log
import vcf


#pylint: disable=C0301
def add_subparser(subparser):
    parser_tag = subparser.add_parser("tag", help="Accepts a directory of VCf results and creates a new directory of VCFs, adding Jacquard-specific FORMAT tags for each VCF record.")
    parser_tag.add_argument("input_dir", help="Path to directory containing VCFs. Other file types ignored")
    parser_tag.add_argument("output_dir", help="Path to Jacquard-tagged VCFs. Will create if doesn't exist and will overwrite files in output directory as necessary")


def tag_files(vcf_readers_to_writers, execution_context):
    total_number_of_files = len(vcf_readers_to_writers)
#     for count, reader, writer in enumerate(vcf_readers_to_writers.items()):
    for count, item in enumerate(vcf_readers_to_writers.items()):
        reader,writer = item
        log("INFO: Reading [{}] ({}/{})", reader.name,
             count, total_number_of_files)
        reader.open()
        writer.open()

        #TODO cgates: method?
        new_headers = reader.metaheaders
        new_headers.extend(execution_context)
        new_headers.append("##jacquard.tag.caller={0}".format(reader.caller.name))
        new_headers.extend(reader.caller.get_new_metaheaders())
        new_headers.append(reader.column_header)
        header_text = "\n".join(new_headers) +"\n"

        writer.write(header_text)
        for vcf_record in reader.vcf_records():
            writer.write(reader.caller.add_tags(vcf_record))

        reader.close()
        writer.close()


def _log_caller_info(vcf_readers):
    caller_count = collections.defaultdict(int)
    for vcf in vcf_readers:
        caller_count[vcf.caller.name] += 1
    for caller_name in sorted(caller_count):
        log("INFO: Recognized [{0}] {1} file(s)",
             caller_count[caller_name], caller_name)


def _build_vcf_readers(input_dir,
                         get_caller=variant_caller_factory.get_caller):
    in_files = sorted(glob.glob(os.path.join(input_dir, "*.vcf")))
    vcf_readers = []
    failures = 0
    for filename in in_files:
        file_path = os.path.join(input_dir, filename)
        try:
            vcf_readers.append(vcf.VcfReader(file_path, get_caller))
        except JQException:
            failures += 1
    if failures:
        raise JQException("[{}] VCF files could not be parsed."
                          " Review logs for details, adjust input, "
                          "and try again.".format(failures))
    _log_caller_info(vcf_readers)
    return vcf_readers


def _build_vcf_readers_to_writers(vcf_readers, output_dir):
    vcf_providers_to_writers = {}
    for reader in vcf_readers:
        basename, extension = os.path.splitext(reader.name)
        new_filename = basename + ".jacquardTags" + extension
        output_filepath = os.path.join(output_dir, new_filename)
        vcf_providers_to_writers[reader] = vcf.VcfWriter(output_filepath)
    
    return vcf_providers_to_writers


def execute(args, execution_context):
    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)
    utils.validate_directories(input_dir, output_dir)

    #TODO cgates: move to jacquard.py
    for line in execution_context:
        log("DEBUG: {}", line)

    vcf_readers = _build_vcf_readers(input_dir)
    if not vcf_readers:
        log("ERROR: Specified input directory [{0}] contains no VCF files."
             "Check parameters and try again.", input_dir)
        #TODO cgates: move to jacquard.py
        shutil.rmtree(output_dir)
        exit(1)

    readers_to_writers = _build_vcf_readers_to_writers(vcf_readers, output_dir)
    log("INFO: Processing [{}] VCF file(s) from [{}]", len(vcf_readers), input_dir)
    tag_files(readers_to_writers, execution_context)
    log("INFO: Wrote [{}] VCF file(s) to [{}]",
         len(readers_to_writers), output_dir)
