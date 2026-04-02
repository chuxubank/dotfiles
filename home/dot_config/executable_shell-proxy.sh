#!/bin/zsh
if [[ "$(uname)" = 'Darwin' ]]; then
    NET_LOCAL=$(networksetup -getcurrentlocation)
fi

if [[ "$NET_LOCAL" = 'Automatic' ]]; then
    if [[ "$HOST_ENV" = 'aa' ]]; then
        echo "http://10.29.248.90:80"
    elif [[ "$HOST_ENV" = 'iv' ]]; then
        echo "http://proxy.invalley.co:8123"
    else
        echo ""
    fi
else
    echo "socks5://127.0.0.1:10800" # Xray
fi

# No Proxy
echo "localhost,127.0.0.1"
