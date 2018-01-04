#!/usr/bin/perl -w 
#
# eprints2dpn_dc_split.pl  - B. Coles.
#
# Last modified 1/4/2018 
#
# PROJECT: Archiving EPrints material to DPN - Step 1 of getting records ready for
#          DPN
#  
# This script reads a file of Dublin Core records exported from eprints, either using
# the batch 'export' command or the Export functionality in the web interface.
#
# It creates individual DC records, each in its own directory.  Directories are named
# according to the eprints ID (e.g. 12345) and DC records are named, for ex.  '12345.dc.txt'
#
# This script should be run *before* the eprints2_dpn_ep3xml_split script, which expects
# directories to be in place.
#
# CONFIGURATION: Before running change the $repo_name variable to the name of
#                the EPrints repo you are processing, e.g. "caltechthesis"
#
#		Also change the $base_url variable, e.g.
#               "https://thesis.library.caltech.edu/"
#
###################################################################################
# 
# Sample input:
#
# title: Interview with Max Delbruck
# creator: Delbruck, Max
# subject: Physics
# subject: All Records
# subject: Biology
# description: Interview in 1978 with Max Delbruck, professor of biology emeritus, begins with his recollections of growing up in an academic family in Berlin.  Trained at Gottingen in the late 1920s as a theoretical physicist, he later switched to biology, inspired by Niels Bohr to investigate the applications of complementarity to biological phenomena.  After postgraduate work at Bristol and Copenhagen, he returned to Berlin in 1932 to work for Lise Meitner and formed a "club" of theoretical physicists, biologists, and biochemists, who met for discussions at his mother's house.  Recollections of the advent of the Nazis in 1933.  In 1937 Delbruck left Berlin for Caltech on a Rockefeller Fellowship; he defends the decision of other German scientists, notably Heisenberg, to remain in Germany.  At Caltech he began working in Drosophila genetics but quickly shifted to phage work with Emory Ellis.  Moved to Vanderbilt University in 1940, where he remained for seven years; comments on Oswald Avery's identification of DNA as the "transforming principle."  Recalls his association with Salvador Luria and summer phage group at Cold Spring Harbor in the 1940s; joint letter with Linus Pauling to Science in 1940 on intermolecular forces in biological processes; his reaction to 1945 publication of Erwin Schrodinger's What is Life?  Returned to Caltech in 1947 as professor of biology; comments on activities of Biology Division under chairmen George W. Beadle and Ray Owen, and the psychobiology of Roger Sperry.  Recalls 1953 Watson-Crick discovery of the structure of DNA; comments on Watson as director of Cold Spring Harbor and on The Double Helix.  Comments on receiving (with Luria and Alfred Hershey) the 1969 Nobel Prize in Physiology or Medicine.  Recalls his later work on Phycomyces.  The interview ends with Delbruck's overview of the history of German science and its travails under the Nazis, and recollections of his postwar visits there.
# date: 1979-01-01
# type: Oral History
# type: NonPeerReviewed
# format: application/pdf
# identifier: http://oralhistories.library.caltech.edu/16/1/OH_Delbruck_M.pdf
# relation: http://resolver.caltech.edu/CaltechOH:OH_Delbruck_M
# identifier:   Delbruck, Max  (1979)  Interview with Max Delbruck.  [Oral History]     http://resolver.caltech.edu/CaltechOH:OH_Delbruck_M <http://resolver.caltech.edu/CaltechOH:OH_Delbruck_M>
# relation: http://oralhistories.library.caltech.edu/16/

#
#############################################################################

use Data::Dumper;
use strict;

# CONFIGURATION - change to EPrints repository name being processed
my $repo_name = "caltechthesis";
my $base_url  = "https://thesis.library.caltech.edu/";  # include trailing /
 
# my $debug = 1;
my $debug = 0;

my $line = 1;
my $input = '';

my $records_created = 0;

my $eprint_number = '';
my $eprint_status = '';

my $output_directory_name;
my $output_file_name;

my $output_record = '';
 
# input file hardcoded for now  - FIXME
open(IN, "<:encoding(UTF-8)", "/coda/dpn/" . $repo_name . "-dc.txt") or die "*** Cannot open /coda/dpn/" . $repo_name . "-dc.txt for input - terminating\n";

while(<IN>)	# loop through input one line at a time

{

        $input = $_;

	if($debug)
	{
		print $input;
	}

	if (($input ne '') && ($input ne ' ') && ($input ne "\n") && ($line > 3))
 	{ 

		if (substr($input,0,6) eq "title:" )   # we have encountered a new record
		{
			#    Create the directory

			#    Write the current $output record to the directory

			if ($output_record ne '') {
				write_record ($output_record, $eprint_number);
		
				$records_created++;
				$output_record = '';
			}
		}

                $output_record .= $input;

		# save the eprint id - will be needed for file/dir naming
		my $len_relation = length($base_url) + length("relation: ");
		if (substr($input,0,$len_relation) eq "relation: " . $base_url )
		{
			$eprint_number = substr($input,$len_relation);
			chomp($eprint_number);  # remove newline at end
			chop($eprint_number);  # remove trailing slash
			if ($debug)
			{
				print "EPRINTID=" . $eprint_number . "\n";
			}
		}
	}
	
	$line++;

}

close(IN);
 
print "NUmber of input lines  processed: $line\n\n";

print "Number of output records created: $records_created\n";



sub write_record {

my $record = shift;
my $dirname = shift;


	my $target_dir = "/coda/dpn/" . $repo_name . "/" . $repo_name . "-" . $dirname;
	my $output_file_name = $repo_name . "-" . $dirname . "-DC.txt";

	mkdir $target_dir;;

	open(DC_OUT, ">:utf8:", $target_dir . "/" . $output_file_name) or die "***cannot open " . $output_file_name. " for writing.\n\n";

	print DC_OUT $record;

	close(DC_OUT);

}
