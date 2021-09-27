#!/bin/bash

#filenames =$(ls '/home/user/Documents/MGTSounds/2020.07.10/id'/*)

copy_to="../testCopy"
simlink_to="../testSimlink"
dont_touch="simlink.sh"

IFS='.'

for entry in *
do 
	echo "$entry"
	read -ra strarr <<< "${entry}"
	ID="${strarr[0]}"
	echo "ID: ${ID}"

	if [ "$entry" != "$dont_touch" ]; then
		echo "copy ${ID} to ${copy_to} and create simlink in ${simlink_to}"
		sudo cp ./"${entry}" "$copy_to" && ln -s "${copy_to}/${entry}" "${simlink_to}/${ID}"
	fi
done