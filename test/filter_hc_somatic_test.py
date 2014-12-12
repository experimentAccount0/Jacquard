# pylint: disable=C0301,C0111
from argparse import Namespace
import glob
import os
import unittest
from StringIO import StringIO
import sys

import jacquard.utils as utils
from testfixtures import TempDirectory
from jacquard.filter_hc_somatic import _write_somatic, _find_somatic_positions
from jacquard.vcf import FileReader
import jacquard.filter_hc_somatic as filter_hc_somatic
import jacquard.logger as logger
import test_case as test_case

VCF_HEADER="#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsampleA\tsampleB\n"

mock_log_called = False
mock_log_messages = []

def mock_log(msg, *args):
    global mock_log_called
    mock_log_called = True
    global mock_log_messages
    mock_log_messages.append(msg.format(*[str(i) for i in args]))

class FilterSomaticTestCase(unittest.TestCase):
    def setUp(self):
        self.output = StringIO()
        self.saved_stderr = sys.stderr
        sys.stderr = self.output
        self.original_info = logger.info
        self.original_error = logger.error
        self.original_warning = logger.warning
        self.original_debug = logger.debug
        self._change_mock_logger()

    def tearDown(self):
        self.output.close()
        sys.stderr = self.saved_stderr
        self._reset_mock_logger()

    def _change_mock_logger(self):
        global mock_log_called
        mock_log_called = False
        global mock_log
        logger.info = mock_log
        logger.error = mock_log
        logger.warning = mock_log
        logger.debug = mock_log

    def _reset_mock_logger(self):
        logger.info = self.original_info
        logger.error = self.original_error
        logger.warning = self.original_warning
        logger.debug = self.original_debug
        global mock_log_messages
        mock_log_messages = []

    def test_findSomaticPositions(self):
        with TempDirectory() as input_dir, TempDirectory() as output_dir:
            input_dir.write("A.snp.vcf","##source=VarScan2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\t"+
                            "INFO\tFORMAT\tNORMAL\tTUMOR\n1\t2352\t.\tA\tG\t.\t.\tfoo\tDP\t234\n1\t2352"+
                            "\t.\tA\tG\t.\t.\tfoo\tDP:JQ_HC_SOM_VS\t234:1\t52:1\n")
            input_dir.write("A.indel.vcf","##source=VarScan2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"+
                            "\tFORMAT\tNORMAL\tTUMOR\n1\t2353\t.\tA\tGT\t.\t.\tfoo\tDP:JQ_HC_SOM_VS\t234:1\t52:1\n")

            file1 = os.path.join(input_dir.path, "A.snp.vcf")
            file2 = os.path.join(input_dir.path, "A.indel.vcf")

            somatic_positions, somatic_positions_header  = _find_somatic_positions([file1, file2], output_dir.path)
            self.assertEqual({'1^2353': 1, '1^2352': 1}, somatic_positions)
            self.assertEqual("##jacquard.filterHCSomatic.total_highConfidence_somatic_positions=2\n", somatic_positions_header)

            input_dir.cleanup()
            output_dir.cleanup()

    def test_filterJQExclude(self):
        with TempDirectory() as input_dir, TempDirectory() as output_dir:
            input_dir.write("A.snp.vcf","##source=VarScan2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\t"+
                            "INFO\tFORMAT\tNORMAL\tTUMOR\n1\t2352\t.\tA\tG\t.\t.\tfoo\tDP\t234\n1\t2352"+
                            "\t.\tA\tG\t.\tJQ_EXCLUDE\tfoo\tDP:JQ_HC_SOM_VS\t234:1\t52:1\n")
            input_dir.write("A.indel.vcf","##source=VarScan2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"+
                            "\tFORMAT\tNORMAL\tTUMOR\n1\t2353\t.\tA\tGT\t.\t.\tfoo\tDP:JQ_HC_SOM_VS\t234:1\t52:1\n")

            file1 = os.path.join(input_dir.path, "A.snp.vcf")
            file2 = os.path.join(input_dir.path, "A.indel.vcf")

            somatic_positions, somatic_positions_header  = _find_somatic_positions([file1, file2], output_dir.path)
            self.assertEqual({'1^2353': 1}, somatic_positions)
            self.assertEqual("##jacquard.filterHCSomatic.total_highConfidence_somatic_positions=1\n", somatic_positions_header)

            input_dir.cleanup()
            output_dir.cleanup()

    def test_filterJQExclude_messages(self):
        with TempDirectory() as input_dir, TempDirectory() as output_dir:
            input_dir.write("A.snp.vcf","##source=VarScan2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\t"+
                            "INFO\tFORMAT\tNORMAL\tTUMOR\n1\t2352\t.\tA\tG\t.\t.\tfoo\tDP\t234\n1\t2352"+
                            "\t.\tA\tG\t.\tJQ_EXCLUDE\tfoo\tDP:JQ_HC_SOM_VS\t234:1\t52:1\n")
            input_dir.write("A.indel.vcf","##source=VarScan2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"+
                            "\tFORMAT\tNORMAL\tTUMOR\n1\t2353\t.\tA\tGT\t.\t.\tfoo\tDP:JQ_HC_SOM_VS\t234:1\t52:1\n")
            input_dir.write("A.snvs.vcf","##source=strelka\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\t"+
                            "INFO\tFORMAT\tSAMPLE\n\t2352\t.\tA\tG\t.\t.\tfoo\tDP\t234\n1\t2352"+
                            "\t.\tA\tG\t.\tJQ_EXCLUDE\tfoo\tDP:JQ_HC_SOM_SK\t234:1")
            input_dir.write("A.indels.vcf","##source=strelka\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"+
                            "\tFORMAT\tSAMPLE\n1\t2353\t.\tA\tGT\t.\t.\tfoo\tDP:JQ_HC_SOM_SK\t234:1\n")

            files = [os.path.join(input_dir.path, "A.snp.vcf"),
                     os.path.join(input_dir.path, "A.indel.vcf"),
                     os.path.join(input_dir.path, "A.snvs.vcf"),
                     os.path.join(input_dir.path, "A.indels.vcf")]

            _find_somatic_positions(files, output_dir.path)

            self.assertIn('Removed [1] problematic VarScan variant records with filter=JQ_EXCLUDE', mock_log_messages)
            self.assertIn('Removed [1] problematic Strelka variant records with filter=JQ_EXCLUDE', mock_log_messages)
            self.assertIn("A total of [2] problematic variant records failed Jacquard's filters. See output and log for details.", mock_log_messages)

    def test_findSomaticPositions_invalidInput(self):
        with TempDirectory() as input_dir, TempDirectory() as output_dir:
            input_dir.write("A.vcf","##source=VarScan2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tNORMAL\tTUMOR\n1\t2352\t.\tA\tG\t.\t.\tfoo\tDP\t234\n1\t2352\t.\tA\tG\t.\t.\tfoo\tDP\t234:1\n")
            input_dir.write("B.vcf","##source=VarScan2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tNORMAL\tTUMOR\n1\t2353\t.\tA\tGT\t.\t.\tfoo\tDP:JQ_SOM_VS\t234:1\n")

            file1 = os.path.join(input_dir.path, "A.vcf")
            file2 = os.path.join(input_dir.path, "B.vcf")

            _find_somatic_positions([file1, file2], output_dir.path)
            self.assertIn('Input file [A.vcf] has no high-confidence somatic variants.', mock_log_messages)
            self.assertIn('Input file [B.vcf] has no high-confidence somatic variants.', mock_log_messages)
            self.assertIn('[2] VCF file(s) had no high-confidence somatic variants. See log for details.', mock_log_messages)

    def test_writeSomatic_outputFileForEachInputFile(self):
        with TempDirectory() as input_dir, TempDirectory() as output_dir:
            input1 = input_dir.write('mutect.vcf', "##MuTect\n"+VCF_HEADER+"1\t32\t.\tA\tT\t.\tPASS\tFOO\tDP\t30")
            input2 = input_dir.write('varscan.vcf', "##source=VarScan2\n"+VCF_HEADER+"1\t35\t.\tA\tG\t.\tPASS\tFOO\tDP\t30")

            in_files = [input1, input2]
            somatic_positions = {"1^32"}
            execution_context = ["##foo", "##bar"]
            _write_somatic(in_files, output_dir.path, somatic_positions, execution_context)

            self.assertEqual(["mutect_HCsomatic.vcf", "varscan_HCsomatic.vcf"], output_dir.actual())
            self.assertIn("Filtered to [1] calls in high-confidence loci.", mock_log_messages)

class FilterHCSomaticFunctionalTestCase(test_case.JacquardBaseTestCase):
    def test_filter_hc_somatic(self):
        with TempDirectory() as output_dir:
            test_dir = os.path.dirname(os.path.realpath(__file__))
            module_testdir = os.path.join(test_dir, "functional_tests", "03_filter_hc_somatic")
            input_dir = os.path.join(module_testdir, "input")

            command = ["filter_hc_somatic", input_dir, output_dir.path, "--force"]
            expected_dir = os.path.join(module_testdir, "benchmark")

            self.assertCommand(command, expected_dir)
