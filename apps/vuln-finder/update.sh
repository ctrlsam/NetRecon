#!/bin/sh

data_dir="dbs"
databases="cve exploitdb openvas osvdb scipvuldb securityfocus securitytracker xforce"

mkdir -p $data_dir

for DB in $databases; do
    wget https://www.computec.ch/projekte/vulscan/download/${DB}.csv -O ${data_dir}/${DB}.csv

    if [ -f ${DB}.csv.1 ]; then
        mv ./${data_dir}/${DB}.csv.1 ./${data_dir}/${DB}.csv
    fi
done
