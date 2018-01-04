#!/usr/bin/perl -w
#
# eprints_ep3xml_split.pl  - B. Coles.
#
# Last modified 1/4/2018 
#
# PROJECT: Archiving EPrints material to DPN - Step 2 in creating Bags for DPN.
#  
# This script reads a file of EP3XML records exported from eprints, either using
# the batch 'export' command or the Export functionality in the web interface.
# It collects records and files in separate directories for each record, suitable
# for later bagging.
#
# NOTE: the script eprints2dpn_dc_split.pl should be run before this script.  It will create
# the directories needed to hold the parts of each EPrints record that are to be bagged.
#
###########################################################################
# CONFIGURATION: change $repo_name variable to name of EPrints repository
#   being processed before running, e.g. "caltechthesis"
#
#               Also change the $curl user variable, to
#               an admin user for the current repo.
#
###########################################################################
# 
# Specific functions:
# 
# 1. It creates individual EP3XML records, each in its own directory.  Directories are named
# according to the eprints ID (e.g. 12345) and XML records are named, for ex.  '12345.xml'.
# If eprints2dpn_dc_split has already been run, these directories will already exist and will
# contain the DC record for this item.
#
# 2. It collects the URLs of all <document> elements in the records and retrieves the
# documents using curl.  These documents are placed in the same directory as the XML record
# and also the DC record produced by the corresponding eprints2dpn_dc_split script, which
# should have been run first to create the directories.
#
# Sample input:
#
# Starting EPrints Repository.
# Connecting to DB ... done.
# <?xml version='1.0' encoding='utf-8'?>
# <eprints xmlns='http://eprints.org/ep2/data/2.0'>
#   <eprint id='http://oralhistories.library.caltech.edu/id/eprint/15'>
#     <eprintid>15</eprintid>
#     <rev_number>7</rev_number>
#     <documents>
#       <document id='http://oralhistories.library.caltech.edu/id/document/643'>
#         <docid>643</docid>
#         <rev_number>2</rev_number>
#         <files>
#           <file id='http://oralhistories.library.caltech.edu/id/file/1684'>
#             <fileid>1684</fileid>
#             <datasetid>document</datasetid>
#             <objectid>643</objectid>
#             <filename>OH_Bonner_J.pdf</filename>
#             <mime_type>application/pdf</mime_type>
#             <hash>c495b7a88582aaa0f07c7a49ea9278af</hash>
#             <hash_type>MD5</hash_type>
#             <filesize>3370653</filesize>
#             <mtime>2015-03-10 20:08:14</mtime>
#             <url>http://oralhistories.library.caltech.edu/15/1/OH_Bonner_J.pdf</url>
#           </file>
#         </files>
#         <eprintid>15</eprintid>
#         <pos>1</pos>
#         <placement>1</placement>
#         <mime_type>application/pdf</mime_type>
#         <format>application/pdf</format>
#         <language>en</language>
#         <security>public</security>
#         <license>other</license>
#         <main>OH_Bonner_J.pdf</main>
#         <content>published</content>
#       </document>
#     </documents>
#     <eprint_status>archive</eprint_status>
#     <userid>1</userid>
#     <dir>disk0/00/00/00/15</dir>
#     <datestamp>2002-10-21</datestamp>
#     <lastmod>2015-03-10 20:08:35</lastmod>
#     <status_changed>2011-10-20 19:44:28</status_changed>
#     <type>oral_history</type>
#     <metadata_visibility>show</metadata_visibility>
#     <item_issues_count>0</item_issues_count>
#     <creators>
#       <item>
#         <name>
#           <family>Bonner</family>
#           <given>James</given>
#         </name>
#         <id>Bonner-J</id>
#       </item>
#     </creators>
#     <title>Interview with James F. Bonner</title>
#     <ispublished>unpub</ispublished>
#     <subjects>
#       <item>name</item>
#       <item>bio</item>
#     </subjects>
#     <full_text_status>public</full_text_status>
#     <abstract>Interview in 1980 with professor of biology James Bonner begins with his re
# collections of growing up in an academic family.  In 1929, his father, a physical chemist
#  at the University of Utah, was a visitor at Caltech, where Bonner enrolled as a junior. 
#  Recalls course work with X-ray crystallographer Roscoe G. Dickinson and activities of Di
# vision of Chemistry and Chemical Engineering under Arthur Amos Noyes; humanities courses 
# with William B. Munro; physics with Earnest Watson, William V. Houston, and Carl Anderson
# ; geology with John P. Buwalda; and biology with Thomas Hunt Morgan, Henry Borsook, and T
# heodosius Dobzhansky.  Became Dobzhansky&apos;s summer researcher and editor; switched fr
# om chemistry to biology.  Graduate work with Dobzhansky on Drosophila genetics and Kennet
# h Thimann on plant hormone auxin.  Friendship with Noyes.  NRC postdoctoral fellowship to
#  Utrecht, Leiden, and ETH, 1934-35.  Joined Caltech&apos;s Biology Division in 1936 as an
#  instructor: recalls colleagues Frits Went, Arie J. Haagen-Smit, Johannes van Overbeek; p
# lant labs at Caltech; coining of term phytotron.  Recollections of Robert A. Millikan.  W
# ar work for U.S. Emergency Rubber Project on guayule and Cryptostegia.  Work on cell biol
# ogy with Sam Wildman; discovery of Fraction 1, central enzyme of photosynthesis.  Foundin
# g of Caltech&apos;s Industrial Associates program in 1950.  Recalls graduate student Paul
#  Tso, discovery of plant actomycin, isolation of ribosomes.  Work of Robert Holley on tra
# nsfer RNAs.  Consultant to Malaysian rubber industry.  &quot;Next 100 Years&quot; project
# , with Harrison Brown.  Studies RNA in 1960s with R. C. Huang and histone chemistry with 
# Douglas Fambrough.  Visitor at Oxford, 1963.  Remarks on underdeveloped countries.  Study
#  of population growth with H. Brown.  Comments on his recent work on cloning genes, and v
# isits to Singapore and China.  His hopes for genetic engineering.  Stint as acting chairm
# an of the Biology Division; comments on Robert L. Sinsheimer.  [See also 1978 joint inter
# view with Bonner, N. H. Horowitz, D. F. Poulson, and S. H. Emerson.]</abstract>
#     <date>1982-01-01</date>
#     <date_type>published</date_type>
#     <id_number>CaltechOH:OH_Bonner_J</id_number>
#     <refereed>FALSE</refereed>
#     <official_url>http://resolver.caltech.edu/CaltechOH:OH_Bonner_J</official_url>
#     <rights>No commercial reproduction, distribution, display or performance rights in th
# is work are provided.</rights>
#     <collection>CaltechOralHistories</collection>
#     <interviewer>Graham Berry</interviewer>
#     <interviewdate>March 13-14, 1980</interviewdate>
#   </eprint>
#
#############################################################################

use Data::Dumper;
use strict;

# my $debug = 1;
my $debug = 0;

# CONFIGURATION: change to repository name of EPrints repo being processed,
#   e.g., "caltechthesis"
my $repo_name = "caltechauthors";
my $curl_user = "admin:admin\@authors";
 
my $line = 1;
my $input = '';

my $records_created = 0;
my $documents_written = 0;

my $eprint_number = '';
my $eprint_status = '';

my $output_directory_name;
my $output_file_name;

my $output_record = '';

my $eprints_xml_header = "<?xml version='1.0' encoding='utf-8'?>\n<eprints xmlns='http://eprints.org/ep2/data/2.0'>\n";

my $eprints_xml_footer = "</eprints>\n";

my @document_urls = '';
my $this_url = '';
my $num_docs = 0;  
 

open(IN, "<:encoding(UTF-8)", "/coda/dpn/" . $repo_name . ".xml") or die "*** Cannot open /coda/dpn/" . $repo_name . ".xml for input - terminating\n";

while(<IN>)	# loop through input one line at a time

{

        $input = $_;

	if($debug)
	{
		print $input;
	}

	# skip lines with no useful content, including first 5 lines
	if (($input ne '') && ($input ne ' ') && ($input ne "\n") && ($line > 5))
 	{ 

		if (substr($input,2,8) eq "<eprint " )   # we have encountered a new record
		{
			#    Write the current $output record to the directory
			if ($output_record ne '') {  
				# add XML header and footer elements
				$output_record = $eprints_xml_header . $output_record .
					$eprints_xml_footer;
				write_record ($output_record, $eprint_number);
		
				$records_created++;
				$output_record = '';

				# fetch all the document files for this record and write
				# them to the same directory
				fetch_docs (\@document_urls, $eprint_number);
				$documents_written += $num_docs;
				$num_docs = 0;
				@document_urls = '';
 
			}
		}

		# Collect data for the curent record
                $output_record .= $input;

		# save the eprint id - will be needed for file/dir naming
		if ( length($input) > 15 )  # don't process short lines 
		{
			if (substr($input,4,10) eq "<eprintid>" )
			{
				$eprint_number = substr($input,14);	
				chomp($eprint_number);   # remove trailing newline
				$eprint_number =~ s/<\/eprintid>//;  # remove trailing end tag
				if ( $debug) 
				{
					print "EPRINTID=" . $eprint_number . "\n";
				}
			}
		}
		
		# save the urls for the document files attached to this eprint
		if ( length($input) > 12 )
		{
			if (substr($input,12,5) eq "<url>" )  
			{
				$this_url = substr($input,17);
				# remove end tag
				$this_url = substr($this_url,0,length($this_url)-7);
				if ($ debug )
 				{
					print "THIS_URL=" . $this_url . "\n";
				}

				$num_docs ++;
				$document_urls[$num_docs-1] = $this_url;
			}
		}
 
	}
	
	$line++;

}

close(IN);
 
print "Number of input lines  processed: $line\n\n";

print "Number of output records created: $records_created\n\n";

print "Number of documents written: $documents_written\n";


sub write_record {

my $record = shift;
my $dirname = shift;

 
	my $target_dir = "/coda/dpn/" . $repo_name . "/" . $repo_name . "-" . $dirname;
	my $output_file_name = $repo_name . "-" . $dirname . ".xml";

#	$target_dir should already exist - created by eprints2dpn_dc_split.pl.  If it's not
#	there, next step will fail.

	open(XML_OUT, ">:utf8", $target_dir . "/" . $output_file_name) or die "***cannot open " . $output_file_name. " for writing.\n\n";

	print XML_OUT $record;

	close(XML_OUT);

}


sub fetch_docs {

my @url = @{$_[0]};
my $dirname = $_[1];

  
	foreach (@url) 
	{

		my $fetch_url = $_;
		my $target_dir = "/coda/dpn/" . $repo_name . "/" . $repo_name . "-" . $dirname;

		# get the filename out of the URL so we can preserve it on output
		my $pos = rindex($fetch_url, '/');
		my $output_file_name = substr($fetch_url, $pos);
	
		# use curl to get the document into a variable for output	
		my $document = `curl -u $curl_user $fetch_url 2>&1`;

	        open(DOC_OUT, ">", $target_dir . "/" . $output_file_name) or die "***cannot open " . $output_file_name. " for writing.\n\n";

		print DOC_OUT $document;
 
		close(DOC_OUT);

	}
}
