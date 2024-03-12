# retry machanism

set -euo pipefail

export RETRY=${RETRY:-10}
export SLEEP_SECONDS=${SLEEP_SECONDS:-900}

RETRY_COUNT=1
while true; do
    echo "$RETRY_COUNT/$RETRY attempt."
    rc=0
    "$@" || rc=$?
    if [[ $rc != 0 ]]; then
        echo "$1 is fail with exit code $rc"
        if [[ $rc == 4 ]]; then
            if [[ $RETRY_COUNT -eq $RETRY ]]; then
                echo "Reach max retry count: $RETRY"
                exit 1
            fi
            echo "sleep for $SLEEP_SECONDS seconds"
            echo "retrying..."
            sleep $SLEEP_SECONDS
            RETRY_COUNT=$((RETRY_COUNT + 1))
            continue
        else
            echo "Unexpected error. Exit code: $rc"
            exit 1
        fi

    else
        break
    fi
done
