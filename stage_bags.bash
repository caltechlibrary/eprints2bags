#!/bin/bash

. thesis.env

KEYS="thesis_ids.keys"

function GetEPrintIDs() {
	if [ ! -f "${KEYS}" ]; then
		mysql "${REPO_ID}" --batch -e 'SELECT eprintid from eprint' | grep -v 'eprintid' >"${KEYS}"
	fi
}

function GetEPrintXML() {
	while read -r KEY; do
		O_DIR="${BAG_PREFIX_PATH}/${KEY}/data"
		O_PATH="${O_DIR}/${KEY}.xml"
		URL="https://${REST_USER}:${REST_PASSWORD}@${HOST}/rest/${KEY}.xml"
		mkdir -p "${O_DIR}"
		if ! curl -H 'Content-Type: application/xml' -o "${O_PATH}" "${URL}"; then
			echo "ERROR: ${KEY}"
			exit 1
		fi
	done <"${KEYS}"
}

function ObjectPath() {
	while read -r KEY; do
		O_DIR="${BAG_PREFIX_PATH}/${KEY}/data"
		P_KEY=$(printf "%08d" "${KEY}")
		P_KEY="$(pairtree encode "${P_KEY}")"
		##echo "DEBUG path >${P_KEY}<"
		OBJECT_PATH="${EPRINT_PREFIX}/${P_KEY}/*"
		if ! scp -r "${FILE_HOST}:${OBJECT_PATH}" "${O_DIR}"; then
			echo "ERROR: writing object ${KEY}"
			exit 1
		fi
	done <"${KEYS}"
}

function CleanupFiles() {
	O_DIR="${BAG_PREFIX_PATH}"
	if [ ! -f trimlist.txt ]; then
		echo "Generating trimlist.txt"
		find "${O_DIR}" -type f |\
			xargs -I {} basename {} |\
			sort |\
			uniq -d |\
			grep -v -E '\.(xml|pdf)$' \
			>trimlist.txt
	else
		echo "Using trimlist.txt"
	fi
	while read -r FNAME; do
		echo "Removing FNAME -> ${FNAME}"
		find "${O_DIR}" -name "${FNAME}" -type f -delete
	done <trimlist.txt
}

echo "Retrieve EPrint IDs"
GetEPrintIDs
echo "Retrieving EPrintXML"
GetEPrintXML
echo "Retrieving digital assets"
ObjectPath
echo "Cleaning up non-assets"
CleanupFiles
