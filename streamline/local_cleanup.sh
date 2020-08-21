#!/bin/bash
# https://stackoverflow.com/a/11279500

bflag="false"
pflag="false"
mflag="false"

usage () { echo "Use the b flag to specify the bucket path, p flag for the code path, and m flag to specify data path"; }

options=':b:m:p:'
while getopts $options option
do
    case "$option" in
      b  ) bflag=$OPTARG;;
      p  ) pflag=$OPTARG;;
      m  ) mflag=$OPTARG;;
      h  ) usage; exit;;
      \? ) echo "Unknown option: -$OPTARG" >&2; exit 1;;
      :  ) echo "Missing option argument for -$OPTARG" >&2; exit 1;;
      *  ) echo "Unimplemented option: -$OPTARG" >&2; exit 1;;
    esac
done

if  [[ $bflag == "false"  || $pflag == "false" ]]
then
  echo "Please specify the b and p flag. Use -h for help."
  exit 1
fi

if [[ $mflag != "false" ]]
then
  echo "Moving data to bucket: $mflag"
fi

echo "executing code for b and p flag: $bflag , $pflag"
