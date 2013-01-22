#!/bin/bash

TARGET_HOST="127.0.0.1"
TARGET_PORT="8080"

function add_tenant {
    curl -v -X POST -d "tenant_id=${1}" "http://${TARGET_HOST}:${TARGET_PORT}/v1/tenant";
}

function remove_tenant {
    curl -v -X DELETE "http://${TARGET_HOST}:${TARGET_PORT}/v1/${1}";
}

function echo_usage {
    echo "${0} <add|remove> [tennant_id]";

    if [ ${#} -gt 0 ]; then
        exit ${1};
    else
        exit 0;
    fi
}

# SCRIPT BEGIN

if [ ${#} -lt 1 ]; then
    echo_usage 1;
fi

while [ "${1}" != "" ]; do
    currentArgument="${1}";
    shift;

    case "${currentArgument}" in
        add)
            add_tenant "${1}";
        ;;

        remove)
            remove_tenant "${1}";
        ;;

        *)
            echo_usage 2;
        ;;
    esac
done

