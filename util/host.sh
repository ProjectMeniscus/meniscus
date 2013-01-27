#!/bin/bash

TARGET_HOST="127.0.0.1"
TARGET_PORT="8080"

function add_host {
    curl -v -X POST -d "{\"hostname\":\"${2}\", \"ip_address\":\"${3}\"}" "http://${TARGET_HOST}:${TARGET_PORT}/v1/tenant/${1}/hosts";
}

function remove_host {
    curl -v  -X DELETE "http://${TARGET_HOST}:${TARGET_PORT}/v1/tenant/${1}/hosts/${2}";
}

function set_profile {
    curl -v -X PUT -d "{\"profile_id\":\"${3}\"}" "http://${TARGET_HOST}:${TARGET_PORT}/v1/tenant/${1}/hosts/${2}"
}

function echo_usage {
    echo "${0} add <tennant_id> <hostname> <host_ip_addr>";
    echo "${0} remove <tennant_id> <host_id>";
    echo "${0} set_profile <tennant_id> <host_id> <profile_id>";

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
            add_host "${1}" "${2}" "${3}";
            exit $?;
        ;;

        remove)
            remove_host "${1}" "${2}";
            exit $?;
        ;;

        set_profile)
            set_profile "${1}" "${2}" "${3}";
            exit $?;
        ;;

        *)
            echo_usage 2;
        ;;
    esac
done

