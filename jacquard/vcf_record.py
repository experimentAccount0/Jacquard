from collections import OrderedDict

class VcfRecord(object):

    def __init__(self, vcf_line):
        vcf_fields = vcf_line.rstrip("\n").split("\t")
        self.chrom,self.pos,self.id,self.ref,self.alt,self.qual,self.filter,self.info,self.format = vcf_fields[0:9]
        self.samples = vcf_fields[9:]
        tags = self.format.split(":")
        self.format_set = tags
        self.sample_dict = {}
        for i,sample in enumerate(self.samples):
            values = sample.split(":")
            self.sample_dict[i] = OrderedDict(zip(tags,values))
    
    def asText(self):
        stringifier = [self.chrom,self.pos,self.id,self.ref,self.alt,self.qual,self.filter,self.info,":".join(self.format_set)]
        for key in self.sample_dict:
            stringifier.append(":".join(self.sample_dict[key].values()))
        return "\t".join(stringifier) + "\n"
    
    def insert_format_field(self, fieldname, field_dict):
        if fieldname in self.format_set:
            raise KeyError
        self.format_set.append(fieldname)
        if (field_dict.keys() != self.sample_dict.keys()):
            raise KeyError()
        for key in self.sample_dict.keys():
            self.sample_dict[key][fieldname] = str(field_dict[key])