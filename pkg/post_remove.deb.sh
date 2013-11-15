#!/bin/sh
# postrm script for meniscus
#
# see: dh_installdeb(1)

set -e

# summary of how this script can be called:
#        * <postrm> `remove'
#        * <postrm> `purge'
#        * <old-postrm> `upgrade' <new-version>
#        * <new-postrm> `failed-upgrade' <old-version>
#        * <new-postrm> `abort-install'
#        * <new-postrm> `abort-install' <old-version>
#        * <new-postrm> `abort-upgrade' <old-version>
#        * <disappearer's-postrm> `disappear' <overwriter>
#          <overwriter-version>
# for details, see http://www.debian.org/doc/debian-policy/ or
# the debian-policy package


case "$1" in
	purge)
        echo "Purging meniscus..." >&2
        if (getent passwd meniscus) > /dev/null 2>&1; then
            userdel meniscus || true
        fi

        if (getent group meniscus) > /dev/null 2>&1; then
            groupdel meniscus || true
        fi

        [ -e /var/lib/meniscus ] && rm -rf /var/lib/meniscus
        [ -e /var/log/meniscus ] && rm -rf /var/log/meniscus
        [ -e /usr/share/meniscus ] && rm -rf /usr/share/meniscus
        [ -e /etc/meniscus ] && rm -rf /etc/meniscus
	;;

    upgrade|failed-upgrade|abort-upgrade)
        echo "upgrade ignored"
    ;;

    remove|abort-install|disappear)
        [ -e /usr/share/meniscus ] && rm -rf /usr/share/meniscus
    ;;

    *)
        echo "postrm called with unknown argument \`$1'" >&2
        exit 1
    ;;
esac

# dh_installdeb will replace this with shell code automatically
# generated by other debhelper scripts.

#DEBHELPER#

exit 0
