#!/bin/zsh
if [[ "$(uname)" = 'Darwin' ]]; then
    NET_LOCAL=$(networksetup -getcurrentlocation)
fi

if [[ "$NET_LOCAL" = 'Work' ]]; then
  echo "http://127.0.0.1:9000" # ZS
else
  echo "socks5://127.0.0.1:10800" # Xray
fi

# No Proxy
echo "localhost,127.0.0.1"
