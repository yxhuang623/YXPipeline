import os

# Make working dir for this pipeline
os.system("mkdir ~/YXpipeline")
os.system("mkdir ~/YXpipeline/reference")
os.system("mkdir ~/YXpipeline/samples")
os.system("mkdir ~/YXpipeline/output_files")

# Obtain the total number of samples for further usage
sranumber = open("SraAccList.txt")
sralist = list(sranumber)
totalsample_numbers = len(sralist)
print(totalsample_numbers)

# Dowanload raw reads
for SRRnumber in sralist:
    SRRnumber = SRRnumber[0:10]
    #os.system("cd /home/yixiao/pipeline-practice/samples")
    command1 = "prefetch " + SRRnumber + " -O ~/YXpipeline/samples"
    os.system(command1)
    command3 = "fasterq-dump -S " + SRRnumber + " -O ~/YXpipeline/samples/" + SRRnumber
    os.system(command3)

# Create path to your original ref file and new ref path which will be generated by this pipeline
os.system("cd YXpipeline")
path = os.path.abspath("YXpipeline")
print(path)
path1 = os.path.abspath("reference_file")
print(path1)

fpath1 = path1 + "/"
rpath1 =[fpath1]
print(rpath1)
for file in os.listdir(path1):
    if file.endswith('.fasta'):
        print(file.__str__())
        rpath1.append(file.__str__())
        print(rpath1)
orirefpath = ''.join(rpath1)
print(orirefpath)

# Copy your input ref file to working place for this pipeline
os.system("cp -r " + orirefpath + " " + path + "/reference")

# Path to the reference
dpath = path + "/reference/"
rpath =[dpath]
print(rpath)
for file in os.listdir(path + "/reference"):
    if file.endswith('.fasta'):
        print(file.__str__())
        rpath.append(file.__str__())
        print(rpath)
referencepath = ''.join(rpath)
print(referencepath)

# Create index file for reference
os.system("bwa index " + referencepath)

# Creating the fasta index file for gatk haplotypecaller
os.system("samtools faidx " + referencepath)
# Creating the FASTA sequence dictionary file
os.system("gatk CreateSequenceDictionary -R " + referencepath)

# Generating raw vcfs and creating pseudo sequence which only include the core genome SNPs
for sample_folder in os.listdir(path + "/samples"):
    print(sample_folder)
    fastqpath = []
    sample_folderpath = path + "/samples/" + sample_folder.__str__()
    print(sample_folderpath)

    if (sample_folder.startswith(".")):
        continue
    else:
        for file in os.listdir(sample_folderpath):
            if (file.endswith(".fastq")):
                fastqpath.append(sample_folderpath + "/" + file.__str__())
        print(fastqpath)
        output_name = sample_folderpath + "/reads.sam"

        # Alignment
        command = "bwa mem " + referencepath + " " + \
                  fastqpath[0] + " " + fastqpath[1] + " > " + output_name
        os.system(command)

        # Convert sam to bam
        bam_name = sample_folderpath + "/YX.unsortedreads.bam"
        command = "samtools view -o " + bam_name + " " + sample_folderpath + "/reads.sam"
        os.system(command)

        # Sort bam
        sorted_name = sample_folderpath + "/YX.sortedreads.bam"
        os.system("samtools sort " + bam_name + " -o " + sorted_name)

        # Removing(marking) duplicates with GATK4
        dupsorted_name = sample_folderpath + "/dupsortedreads.bam"
        mdupsorted_name = sample_folderpath + "/dedup.metrics.txt"
        command = "gatk MarkDuplicates I=" + sorted_name + " O=" + dupsorted_name + \
                  " M=" + mdupsorted_name
        os.system(command)

        # Samtools mpileup
        pileup_name = sample_folderpath + "/mpileup.pileup"
        command = "samtools mpileup -f " + referencepath + " " + dupsorted_name + " -o " + pileup_name
        os.system(command)

        # Remove sam and bam files to save the storage
        os.system("rm " + output_name)
        os.system("rm " + bam_name)
        os.system("rm " + sorted_name)
        os.system("rm " + dupsorted_name)

        # Generate raw snp_vcf files
        snpvcf_file_name = sample_folderpath + "/snpvar.vcf"
        command = "varscan mpileup2snp " + pileup_name + " > " + \
                  snpvcf_file_name + " --min-var-freq 0.90 --output-vcf 1"
        os.system(command)

        # Generate raw cns_vcf files
        vcf_file_name = sample_folderpath + "/var.vcf"
        command = "varscan mpileup2cns " + pileup_name + " > " + \
                  vcf_file_name + " --min-var-freq 0.90 --output-vcf 1"
        os.system(command)
        # Remove pileup file to save the storage
        #os.system("rm " + pileup_name)

# Creat a list which contain all the SNP sites
rawsnpsitsnumber = []
for sample_folder in os.listdir(path + "/samples"):
    print(sample_folder)
    fastqpath = []
    sample_folderpath = path + "/samples/" + sample_folder.__str__()
    print(sample_folderpath)
    open_vcffile = open(sample_folderpath + "/snpvar.vcf", 'r')
    vcfline = open_vcffile.readline()
    while (vcfline):
        if (vcfline[0] != "#"):
            column = vcfline.split("\t")
            rawsnpsitsnumber.append(column[1])
        vcfline = open_vcffile.readline()
    open_vcffile.close()
snpsitsnumber = list(set(rawsnpsitsnumber))
snpsitsnumber.sort()
print(snpsitsnumber)
print(len(snpsitsnumber))

# Extract the core genome SNP sites
need_sites =[]
for sample_folder in os.listdir(path + "/samples"):
    print(sample_folder)
    willaddsites = []
    snponlysite = []
    sample_folderpath = path + "/samples/" + sample_folder.__str__()
    varvcf = open(sample_folderpath + "/var.vcf", 'r')
    vline = varvcf.readline()
    while (vline):
        if (vline[0] != "#"):
            column = vline.split("\t")
            if column[1] in snpsitsnumber:
                need_sites.append(column[1])
        vline = varvcf.readline()
    varvcf.close()
print(len(need_sites))

realsites =[]
for i in need_sites:
    if int(need_sites.count(i)) == totalsample_numbers:
        realsites.append(i)
Rrealsites = list(set(realsites))
print(Rrealsites)
print("The length of  pseudo sequence will be:")
print(len(Rrealsites))
Rrealsites.sort()

# Create pseudo-sequence which contains the core genome SNP sites for each sample
for sample_folder in os.listdir(path + "/samples"):
    print(sample_folder)
    willaddsites = []
    snponlysite = []
    sample_folderpath = path + "/samples/" + sample_folder.__str__()

    # Find the REF and ALT bases at SNP sites
    varvcf = open(sample_folderpath + "/var.vcf", 'r')
    newvarvcf = open(sample_folderpath + "/prepsuedo.vcf", 'w')
    vline = varvcf.readline()
    while (vline):
        if (vline[0] != "#"):
            column = vline.split("\t")
            if column[1] in Rrealsites:
                newvarvcf.write(vline)
        vline = varvcf.readline()
    varvcf.close()
    newvarvcf.close()

    # Replace the ALT marked "." with REF base
    prepsuedovcf = open(sample_folderpath + "/prepsuedo.vcf", 'r')
    pline = prepsuedovcf.readline()
    psuedovcf = open(sample_folderpath + "/psuedo.vcf", 'w')
    while(pline):
        column = pline.split("\t")
        if column[4] == ".":
            #and column[4] != "G" and column[4] != "C" and column[4] != "T
            pline = pline.replace(column[4], column[3], 3)
            psuedovcf.write(pline)
        else:
            psuedovcf.write(pline)
        pline = prepsuedovcf.readline()
    psuedovcf.close()
    prepsuedovcf.close()

    # Generate the final pseudo-sequence vcf file for each sample
    psuedo_file = open(sample_folderpath + "/psuedo.vcf", "r")
    ppline = psuedo_file.readline()
    pseudo_seq_list = []
    while (ppline):
        token = ppline.split("\t")
        pseudo_seq_list.append(token[4])
        ppline = psuedo_file.readline()
    pseudo_seq_str = ''.join(pseudo_seq_list)
    psuedo_file.close()

    # Write the title and pseudo_sequence into fasta file
    pse_output_name = sample_folderpath + "/pseudo.fasta"
    pse_output_file = open(pse_output_name, "w")
    pse_output_file.write(">" + sample_folderpath[32:] + "\n")
    pse_output_file.write(pseudo_seq_str + "\n")
    pse_output_file.close()

# Create snp 'matrix' --combine files of consensus.fasta into single fasta file
pseq_list = []
for sample_folder in os.listdir(path + "/samples"):
    sample_folderpath = path + "/samples/" + sample_folder
    print(sample_folderpath)
    snpma_output_file = path + "/snpmatrix.fasta"
    opsnpma_output_file = open(snpma_output_file, "w")
    pseq_list.append(sample_folderpath + "/pseudo.fasta")
    print(pseq_list)
    for pseq_file_path in pseq_list:
        input_file = open(pseq_file_path, "r")
        line = input_file.readline()
        while (line):
            if line.startswith(">"):
                opsnpma_output_file.writelines(line)
            else:
                opsnpma_output_file.writelines(line)
            line = input_file.readline()
    opsnpma_output_file.close()



