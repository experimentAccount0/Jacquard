# pylint: disable=line-too-long,too-many-public-methods,too-few-public-methods
# pylint: disable=invalid-name,global-statement
from jacquard import __version__
from jacquard.variant_callers import varscan
from jacquard.variant_callers.varscan import _HCTag
from test.vcf_test import MockFileReader, MockVcfReader
import jacquard.vcf as vcf
import test.test_case as test_case


class HCTagTestCase(test_case.JacquardBaseTestCase):
    def test_add_tag_values_highConfidenceDoesNotChangeFilter(self):
        record = vcf.VcfRecord("chr1", "42", "ref", "alt", vcf_filter="pass")
        input_reader = MockFileReader("foo.txt", ["chrom\tposition\tref\tvar",
                                                  "chr1\t42\tref\tvar",
                                                  "chr2\t50\tref\tvar"])
        expected = "pass"
        actual = _HCTag(input_reader).add_tag_values(record).filter
        self.assertEquals(expected, actual)

    def test_add_tag_values_lowConfidencePassingReplacesFilter(self):
        record = vcf.VcfRecord("chr1", "30", "ref", "alt", vcf_filter="pass")
        input_reader = MockFileReader("foo.txt", ["chrom\tposition\tref\tvar",
                                                  "chr1\t42\tref\tvar",
                                                  "chr2\t50\tref\tvar"])
        tag = _HCTag(input_reader)
        expected = tag._TAG_ID
        actual = tag.add_tag_values(record).filter
        self.assertEquals(expected, actual)


class AlleleFreqTagTestCase(test_case.JacquardBaseTestCase):
    def test_metaheader(self):
        self.assertEqual('##FORMAT=<ID={0}AF,Number=A,Type=Float,Description="Jacquard allele frequency for VarScan: Decimal allele frequency rounded to 2 digits (based on FREQ)",Source="Jacquard",Version={1}>'.format(varscan.JQ_VARSCAN_TAG, __version__),
                         varscan._AlleleFreqTag().metaheader)

    def test_format_missingAFTag(self):
        tag = varscan._AlleleFreqTag()
        line = "CHROM|POS|ID|REF|ALT|QUAL|FILTER|INFO|F1:F2:F3|SA.1:SA.2:SA.3|SB.1:SB.2:SB.3\n".replace('|', "\t")
        originalVcfRecord = vcf.VcfRecord.parse_record(line, ["SA", "SB"])
        processedVcfRecord = vcf.VcfRecord.parse_record(line, ["SA", "SB"])
        tag.add_tag_values(processedVcfRecord)
        self.assertEquals(originalVcfRecord.text(), processedVcfRecord.text())

    def test_format_presentAFTag(self):
        tag = varscan._AlleleFreqTag()
        line = "CHROM|POS|ID|REF|ALT|QUAL|FILTER|INFO|FREQ:F2:F3|56.7%:SA.2:SA.3|83.4%:SB.2:SB.3\n".replace('|', "\t")
        expected = "CHROM|POS|ID|REF|ALT|QUAL|FILTER|INFO|FREQ:F2:F3:{0}AF|56.7%:SA.2:SA.3:0.57|83.4%:SB.2:SB.3:0.83\n".format(varscan.JQ_VARSCAN_TAG).replace('|', "\t")
        processedVcfRecord = vcf.VcfRecord.parse_record(line, ["SA", "SB"])
        tag.add_tag_values(processedVcfRecord)
        self.assertEquals(expected, processedVcfRecord.text())

    def test_format_multAlt(self):
        tag = varscan._AlleleFreqTag()
        line = "CHROM|POS|ID|REF|ALT|QUAL|FILTER|INFO|FREQ:F2:F3|56.7%,41%:SA.2:SA.3|83.4%,23%:SB.2:SB.3\n".replace('|', "\t")
        expected = "CHROM|POS|ID|REF|ALT|QUAL|FILTER|INFO|FREQ:F2:F3:{0}AF|56.7%,41%:SA.2:SA.3:0.57,0.41|83.4%,23%:SB.2:SB.3:0.83,0.23\n".format(varscan.JQ_VARSCAN_TAG).replace('|', "\t")
        processedVcfRecord = vcf.VcfRecord.parse_record(line, ["SA", "SB"])
        tag.add_tag_values(processedVcfRecord)
        self.assertEquals(expected, processedVcfRecord.text())


class DepthTagTestCase(test_case.JacquardBaseTestCase):
    def test_metaheader(self):
        self.assertEqual('##FORMAT=<ID={0}DP,Number=1,Type=Float,Description="Jacquard depth for VarScan (based on DP)",Source="Jacquard",Version={1}>'.format(varscan.JQ_VARSCAN_TAG, __version__),
                         varscan._DepthTag().metaheader)

    def test_format_missingDPTag(self):
        tag = varscan._DepthTag()
        line = "CHROM|POS|ID|REF|ALT|QUAL|FILTER|INFO|F1:F2:F3|SA.1:SA.2:SA.3|SB.1:SB.2:SB.3\n".replace('|', "\t")
        originalVcfRecord = vcf.VcfRecord.parse_record(line, ["SA", "SB"])
        processedVcfRecord = vcf.VcfRecord.parse_record(line, ["SA", "SB"])
        tag.add_tag_values(processedVcfRecord)
        self.assertEquals(originalVcfRecord.text(), processedVcfRecord.text())

    def test_format_presentDPTag(self):
        tag = varscan._DepthTag()
        line = "CHROM|POS|ID|REF|ALT|QUAL|FILTER|INFO|DP:F2:F3|2:SA.2:SA.3|4:SB.2:SB.3\n".replace('|', "\t")
        expected = "CHROM|POS|ID|REF|ALT|QUAL|FILTER|INFO|DP:F2:F3:{0}DP|2:SA.2:SA.3:2|4:SB.2:SB.3:4\n".format(varscan.JQ_VARSCAN_TAG).replace('|', "\t")
        processedVcfRecord = vcf.VcfRecord.parse_record(line, ["SA", "SB"])
        tag.add_tag_values(processedVcfRecord)
        self.assertEquals(expected, processedVcfRecord.text())


class SomaticTagTestCase(test_case.JacquardBaseTestCase):
    def test_metaheader(self):
        self.assertEqual('##FORMAT=<ID={0}HC_SOM,Number=1,Type=Integer,Description="Jacquard somatic status for VarScan: 0=non-somatic,1=somatic (based on SOMATIC info tag and if sample is TUMOR)",Source="Jacquard",Version={1}>'.format(varscan.JQ_VARSCAN_TAG, __version__),
                         varscan._SomaticTag().metaheader)

    def test_format_missingSSTag(self):
        tag = varscan._SomaticTag()
        line = "CHROM|POS|ID|REF|ALT|QUAL|FILTER|INFO|F1:F2:F3|SA.1:SA.2:SA.3|SB.1:SB.2:SB.3\n".replace('|', "\t")
        expected = ("CHROM|POS|ID|REF|ALT|QUAL|FILTER|INFO|F1:F2:F3:{0}HC_SOM|SA.1:SA.2:SA.3:0|SB.1:SB.2:SB.3:0\n").format(varscan.JQ_VARSCAN_TAG).replace('|', "\t")
        processedVcfRecord = vcf.VcfRecord.parse_record(line, ["SA", "SB"])
        tag.add_tag_values(processedVcfRecord)
        self.assertEquals(expected, processedVcfRecord.text())

    def test_format_presentSSTag_withHC(self):
        tag = varscan._SomaticTag()
        line = "CHROM|POS|ID|REF|ALT|QUAL|PASS|SS=2|F1:F2:F3|2:SA.2:SA.3|SB.1:SB.2:SB.3\n".replace('|', "\t")
        expected = "CHROM|POS|ID|REF|ALT|QUAL|PASS|SS=2|F1:F2:F3:{0}HC_SOM|2:SA.2:SA.3:0|SB.1:SB.2:SB.3:1\n".format(varscan.JQ_VARSCAN_TAG).replace('|', "\t")
        processedVcfRecord = vcf.VcfRecord.parse_record(line, ["SA", "SB"])
        tag.add_tag_values(processedVcfRecord)
        self.assertEquals(expected, processedVcfRecord.text())

    def test_format_presentSSTag_withoutHCManyFilters(self):
        tag = varscan._SomaticTag()
        line = "CHROM|POS|ID|REF|ALT|QUAL|{0};foo|SS=2|F1:F2:F3|2:SA.2:SA.3|SB.1:SB.2:SB.3\n".format(varscan._HCTag._TAG_ID).replace('|', "\t")
        expected = "CHROM|POS|ID|REF|ALT|QUAL|{0};foo|SS=2|F1:F2:F3:{1}HC_SOM|2:SA.2:SA.3:0|SB.1:SB.2:SB.3:0\n".format(varscan._HCTag._TAG_ID, varscan.JQ_VARSCAN_TAG).replace('|', "\t")
        processedVcfRecord = vcf.VcfRecord.parse_record(line, ["SA", "SB"])
        tag.add_tag_values(processedVcfRecord)
        self.assertEquals(expected, processedVcfRecord.text())

    def test_format_presentSSTag_withoutHC(self):
        tag = varscan._SomaticTag()
        line = "CHROM|POS|ID|REF|ALT|QUAL|{0}|SS=2|F1:F2:F3|2:SA.2:SA.3|SB.1:SB.2:SB.3\n".replace('|', "\t").format(varscan._HCTag._TAG_ID)
        expected = "CHROM|POS|ID|REF|ALT|QUAL|{0}|SS=2|F1:F2:F3:{1}HC_SOM|2:SA.2:SA.3:0|SB.1:SB.2:SB.3:0\n".format(varscan._HCTag._TAG_ID, varscan.JQ_VARSCAN_TAG).replace('|', "\t")
        processedVcfRecord = vcf.VcfRecord.parse_record(line, ["SA", "SB"])
        tag.add_tag_values(processedVcfRecord)
        self.assertEquals(expected, processedVcfRecord.text())

    def test_format_SSTag_notEqual2(self):
        tag = varscan._SomaticTag()
        line = "CHROM|POS|ID|REF|ALT|QUAL|PASS|SS=5|F1:F2:F3|2:SA.2:SA.3|SB.1:SB.2:SB.3\n".replace('|', "\t")
        expected = "CHROM|POS|ID|REF|ALT|QUAL|PASS|SS=5|F1:F2:F3:{0}HC_SOM|2:SA.2:SA.3:0|SB.1:SB.2:SB.3:0\n".format(varscan.JQ_VARSCAN_TAG).replace('|', "\t")
        processedVcfRecord = vcf.VcfRecord.parse_record(line, ["SA", "SB"])
        tag.add_tag_values(processedVcfRecord)
        self.assertEquals(expected, processedVcfRecord.text())


class VarscanTestCase(test_case.JacquardBaseTestCase):
    def setUp(self):
        super(VarscanTestCase, self).setUp()
        self.caller = varscan.Varscan()

    @staticmethod
    def append_hc_files(readers, file1="snp.somatic.hc.fpfilter.pass", file2="indel.somatic.hc.fpfilter.pass", content1=None, content2=None):
        if not content1:
            content1 = []
        if not content2:
            content2 = []
        readers.append(MockFileReader(file1, content1))
        readers.append(MockFileReader(file2, content2))

    @staticmethod
    def _get_tag_class_names(vcf_reader):
        return [tag.__class__.__name__ for tag in vcf_reader.tags]

    def test_claim_multiple_patients(self):
        record1 = "chr1\t.\t.\t.\t.\t.\t.\t.\t."
        content1 = ["##foo", "##source=VarScan2", "#chrom", record1]
        content2 = ["chrom\tposition", "1\t23"]
        reader1 = MockFileReader("p2.fileA.vcf", content1)
        reader2 = MockFileReader("p2.fileB.vcf", content1)
        reader3 = MockFileReader("p2.fileA.Somatic.hc.fpfilter.pass", content2)
        reader4 = MockFileReader("p3.fileA.vcf", content1)
        file_readers = [reader1, reader2, reader3, reader4]

        caller = varscan.Varscan()
        dummy, vcf_readers = caller.claim(file_readers)

        self.assertEquals(3, len(vcf_readers))
        self.assertIsInstance(vcf_readers[0], varscan._VarscanVcfReader)
        self.assertEquals("p2.fileA.vcf", vcf_readers[0]._vcf_reader.file_name)
        self.assertIn("_HCTag",
                      self._get_tag_class_names(vcf_readers[0]))
        self.assertNotIn("_HCTag",
                         self._get_tag_class_names(vcf_readers[1]))
        self.assertNotIn("_HCTag",
                         self._get_tag_class_names(vcf_readers[2]))
        self.assertEquals(reader1.file_name, vcf_readers[0]._vcf_reader.file_name)

    def test_claim_varscan_vcf_only(self):
        record1 = "chr1\t.\t.\t.\t.\t.\t.\t.\t."
        content1 = ["##foo", "##MuTect=123", "#chrom", record1]
        content2 = ["##foo", "##source=VarScan2", "#chrom", record1]
        reader1 = MockFileReader("fileA.vcf", content1)
        reader2 = MockFileReader("fileB.vcf", content2)
        file_readers = [reader1, reader2]

        caller = varscan.Varscan()
        unrecognized_readers, vcf_readers = caller.claim(file_readers)

        self.assertEquals(1, len(unrecognized_readers))
        self.assertEquals([reader1], unrecognized_readers)
        self.assertEquals(1, len(vcf_readers))
        self.assertIsInstance(vcf_readers[0], varscan._VarscanVcfReader)

        self.assertEquals(reader2.file_name, vcf_readers[0]._vcf_reader.file_name)

    def test_claim_vcf_and_filter_file(self):
        record1 = "chr1\t.\t.\t.\t.\t.\t.\t.\t."
        content1 = [self.entab("chrom|position|ref|var"),
                    record1]
        content2 = ["##foo", "##source=VarScan2", "#chrom", record1]
        reader1 = MockFileReader("patientA.indel.Somatic.hc.fpfilter.pass", content1)
        reader2 = MockFileReader("patientA.indel.vcf", content2)
        reader3 = MockFileReader("patientA.snp.Somatic.hc.fpfilter.pass", content1)
        reader4 = MockFileReader("patientA.snp.vcf", content2)
        reader5 = MockFileReader("patientA.readme", ["foo"])
        file_readers = [reader1, reader2, reader3, reader4, reader5]

        caller = varscan.Varscan()
        unrecognized_readers, vcf_readers = caller.claim(file_readers)

        self.assertEquals(1, len(unrecognized_readers))
        self.assertEquals([reader5], unrecognized_readers)
        self.assertEquals(2, len(vcf_readers))
        self.assertIsInstance(vcf_readers[0], varscan._VarscanVcfReader)
        self.assertEquals(reader2.file_name, vcf_readers[0]._vcf_reader.file_name)
        self.assertEquals(reader1.file_name, vcf_readers[0]._som_hc_file_reader.file_name)
        self.assertIsInstance(vcf_readers[1], varscan._VarscanVcfReader)
        self.assertEquals(reader4.file_name, vcf_readers[1]._vcf_reader.file_name)
        self.assertEquals(reader3.file_name, vcf_readers[1]._som_hc_file_reader.file_name)

    def test_claim_heterogeneous_vcfs_and_filter_files(self):
        record1 = "chr1\t.\t.\t.\t.\t.\t.\t.\t."
        content1 = [self.entab("chrom|position|ref|var"),
                    record1]
        content2 = ["##foo", "##source=VarScan2", "#chrom", record1]
        reader1 = MockFileReader("patientA.indel.Somatic.hc.fpfilter.pass", content1)
        reader2 = MockFileReader("patientA.indel.vcf", content2)
        reader3 = MockFileReader("patientA.UNCLAIMED.Somatic.hc.fpfilter.pass", content1)
        reader4 = MockFileReader("patientA.singleton.vcf", content2)
        file_readers = [reader1, reader2, reader3, reader4]

        caller = varscan.Varscan()
        unrecognized_readers, vcf_readers = caller.claim(file_readers)

        self.assertEquals(1, len(unrecognized_readers))
        self.assertEquals("patientA.UNCLAIMED.Somatic.hc.fpfilter.pass",
                          unrecognized_readers[0].file_name)
        self.assertEquals(2, len(vcf_readers))
        self.assertIsInstance(vcf_readers[0], varscan._VarscanVcfReader)
        self.assertEquals(reader2.file_name, vcf_readers[0]._vcf_reader.file_name)
        self.assertEquals(reader1.file_name, vcf_readers[0]._som_hc_file_reader.file_name)
        self.assertIsInstance(vcf_readers[1], varscan._VarscanVcfReader)
        self.assertEquals(reader4.file_name, vcf_readers[1]._vcf_reader.file_name)
        self.assertEquals(None, vcf_readers[1]._som_hc_file_reader)

    def test_claim_ignores_unpaired_non_vcf_files(self):
        record1 = "chr1\t.\t.\t.\t.\t.\t.\t.\t."
        content1 = ["##foo", "##source=VarScan2", "#chrom", record1]
        reader1 = MockFileReader("fileA.txt", content1)
        file_readers = [reader1]

        caller = varscan.Varscan()
        unrecognized_readers, vcf_readers = caller.claim(file_readers)

        self.assertEquals(1, len(unrecognized_readers))
        self.assertEquals([reader1], unrecognized_readers)
        self.assertEquals(0, len(vcf_readers))

    def test_get_files_per_patient(self):
        reader1 = MockFileReader("p1.fileA.txt")
        reader2 = MockFileReader("p1.fileB.txt")
        reader3 = MockFileReader("p2.fileA.txt")
        reader4 = MockFileReader("p2.fileB.txt")
        actual_patient_dict = varscan.Varscan._get_files_per_patient([reader1,
                                                                      reader2,
                                                                      reader3,
                                                                      reader4])
        expected_patient_dict = {"p1": [reader1, reader2],
                                 "p2": [reader3, reader4]}

        self.assertEquals(expected_patient_dict.keys(), dict(actual_patient_dict).keys())
        self.assertEquals(expected_patient_dict.values(), dict(actual_patient_dict).values())


class VarscanVcfReaderTestCase(test_case.JacquardBaseTestCase):
    def test_metaheaders(self):
        vcf_reader = MockVcfReader(metaheaders=["##foo", "##source=VarScan2"])
        varscan_vcf_reader = varscan._VarscanVcfReader(vcf_reader)
        metaheaders = varscan_vcf_reader.metaheaders

        self.assertIn(varscan._AlleleFreqTag().metaheader, metaheaders)
        self.assertIn(varscan._DepthTag().metaheader, metaheaders)
        self.assertIn(varscan._SomaticTag().metaheader, metaheaders)
        self.assertIn("##foo", metaheaders)
        self.assertIn("##source=VarScan2", metaheaders)
        self.assertIn("##jacquard.translate.caller=VarScan", metaheaders)

    def test_vcf_records_newTagsPresent(self):
        record1 = vcf.VcfRecord(chrom="chr1",
                                pos="21",
                                ref="A",
                                alt="G",
                                sample_tag_values={"sampleA": {"DP": "45"},
                                                   "sampleB": {"DP": "67"}})
        record2 = vcf.VcfRecord(chrom="chr1",
                                pos="22",
                                ref="A",
                                alt="G",
                                sample_tag_values={"sampleA": {"FREQ": "46%"},
                                                   "sampleB": {"FREQ": "68%"}})
        vcf_reader = MockVcfReader(records=[record1, record2])

        varscan_vcf_reader = varscan._VarscanVcfReader(vcf_reader)
        vcf_records = [record for record in varscan_vcf_reader.vcf_records()]

        self.assertEquals(2, len(vcf_records))

        self.assertIn("DP", vcf_records[0].format_tags)
        self.assertIn(varscan.JQ_VARSCAN_TAG + "DP", vcf_records[0].format_tags)
        self.assertIn(varscan.JQ_VARSCAN_TAG + "HC_SOM", vcf_records[0].format_tags)
        self.assertIn(varscan.JQ_VARSCAN_TAG + "CALLER_REPORTED", vcf_records[0].format_tags)
        self.assertIn(varscan.JQ_VARSCAN_TAG + "CALLER_PASSED", vcf_records[0].format_tags)

        self.assertIn("FREQ", vcf_records[1].format_tags)
        self.assertIn(varscan.JQ_VARSCAN_TAG + "AF", vcf_records[1].format_tags)
        self.assertIn(varscan.JQ_VARSCAN_TAG + "HC_SOM", vcf_records[1].format_tags)
        self.assertIn(varscan.JQ_VARSCAN_TAG + "CALLER_REPORTED", vcf_records[1].format_tags)
        self.assertIn(varscan.JQ_VARSCAN_TAG + "CALLER_PASSED", vcf_records[1].format_tags)


    def test_vcf_records_SomHcFileSNP(self):
        record1 = vcf.VcfRecord(chrom="chr1", pos="21", ref="A", alt="G", vcf_filter="PASS")
        record2 = vcf.VcfRecord(chrom="chr1", pos="22", ref="A", alt="T", vcf_filter="PASS")
        vcf_reader = MockVcfReader(records=[record1, record2])

        content1 = ["chrom\tposition",
                    "chr1\t21",
                    "chr1\t22"]
        somatic_hc_reader = MockFileReader("fileA.Somatic.hc.fpfilter.pass", content1)

        varscan_vcf_reader = varscan._VarscanVcfReader(vcf_reader, somatic_hc_reader)
        vcf_records = [record for record in varscan_vcf_reader.vcf_records()]

        self.assertEquals(2, len(vcf_records))
        self.assertIn("PASS", vcf_records[0].filter)
        self.assertIn("PASS", vcf_records[1].filter)

    def test_open_and_close(self):
        vcf_reader = MockVcfReader(metaheaders=["##foo", "##source=VarScan2"])
        varscan_vcf_reader = varscan._VarscanVcfReader(vcf_reader)
        varscan_vcf_reader.open()
        varscan_vcf_reader.close()

        self.assertTrue(varscan_vcf_reader.open)
        self.assertTrue(varscan_vcf_reader.close)
