# eprints2dpn

Tools for moving EPrints (CODA) materials to DPN.

See documentation in Library WIKI on Confluence for usage information:
https://caltechlibrary.atlassian.net/wiki/spaces/DP/pages/233799716/DPN+Workflow

Briefly, functions are as follows:

Material in EPrints must be extracted before it can be moved to DPN.  First you need to gather the EP3XML metadata which contains all of the fields in the records as well as pointers to the associated files.  You should also collect Dublin Core, and you may want other forms of metadata as well.

- Use the EPrints batch export command (<EPRINTS_ROOT>/bin/export) with an appropriate plugin parameter to get the desired kind of metadata.  You will get one large file with all records.

- Use the EPrints web interface export to export EP3XML (and optionally other formats) via file download.

- Consult with Robert about using his EPrints tools to extract appropriate metadata according to arbitrary criteria.

Metadata files then need to be processed with tools available in the eprints2dpn GitHub repository.  These consist of

_eprints2dpn_dc_split.pl_ which takes the file of DC records and splits them into one record per item.  Each record is stored in its own directory named after the eprintid of the item. The individual metadata files are also named after the eprintid, e.g. 1234-DC.txt.  Run this script first, since the next script depends on the individual directories already existing.

_eprints2dpn_ep3xml_split.pl_ which splits the EP3XML file into individual records as well.  These go into the correct directories created in the previous step.  This script also performs the crucial step of retrieving the document files attached to the item, using curl.  These files also go into the individual directories, so each item now has DC, EP3XML, and document file(s) in one directory.

_bag_for_dpn.sh_ - shell script to bag the contents of each directory.  CAUTION: This script is destructive in that it replaces the directories with bags.  It also always runs in the current directory, so make sure you are in the right place before running it.  TODO: Add safety checks to this script!
