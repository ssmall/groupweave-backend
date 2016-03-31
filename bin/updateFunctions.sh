#!/bin/bash -e

BIN_DIR=$(dirname $0)
BASE_DIR="${BIN_DIR}/.."
ZIPFILE="groupweave-backend.zip"

cd "$BASE_DIR"

update_function(){
    aws --region="us-east-1" lambda update-function-code --function-name "$1" \
                                    --zip-file "fileb://$ZIPFILE"
}

zip -r "$ZIPFILE" ./* -x tests/ cli/ bin/ tests/* cli/* bin/* *.txt


while IFS='' read -r line || [[ -n "$line" ]]; do
    update_function "$line"
done < ".lambda_functions"