set -e
TMPFILE=$(mktemp)
trap "cat $TMPFILE; rm $TMPFILE" EXIT

function pl() {
    CURRENT=$(plutil -extract $1 raw $TMPFILE 2>/dev/null || :)
    if [ "$CURRENT" != "$3" ]; then
        plutil -replace $* "$TMPFILE"
    fi
}

cat <&0 >$TMPFILE

if [ ! -s $TMPFILE ]; then
    plutil -create binary1 $TMPFILE
fi
