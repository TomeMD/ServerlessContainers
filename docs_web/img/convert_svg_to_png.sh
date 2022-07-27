#!/bin/bash

function convert(){
    for filename in $(find *.svg 2> /dev/null); do
        new_file=$(basename $filename .svg)
        inkscape -z -e $new_file.png -d 600 $filename -D
    done
}

convert
inkscape -z -e favicon.ico -d 600 icon.svg -D

cd architecture
convert
cd ..

cd configuration
convert
cd ..

cd deployment
convert
cd ..

cd quickstart
convert
cd ..

cd use_case
convert
cd ..
