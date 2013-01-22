#!/bin/bash

TARGET_HOST="127.0.0.1"
TARGET_PORT="8080"

function add_tenant {
    curl -v -X POST -d "tenant_id=${1}" "http://${TARGET_HOST}:${TARGET_PORT}/v1/tenant";
}

function remove_tenant {
    curl -v -X DELETE "http://${TARGET_HOST}:${TARGET_PORT}/v1/${1}";
}

function add_profile {
    curl -v -X POST -d "name=${2}" "http://${TARGET_HOST}:${TARGET_PORT}/v1/${1}/profiles";
}

function echo_usage {
    echo "${0} <add|remove> <tennant_id>";
    echo "${0} <add_profile> <tennant_id> <profile_name>";

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
            exit $?;
        ;;

        remove)
            remove_tenant "${1}";
            exit $?;
        ;;

        add_profile)
            add_profile "${1}" "${2}"
            exit $?;
        ;;
        
        *)
            echo_usage 2;
        ;;
    esac
done

