# gnupg upgrades leave old daemons running; kill them so the new binaries attach.
gpgk() {
  command gpgconf --kill all
}

gpg_version() {
  command gpg --version 2>/dev/null | awk 'NR==1 { print; exit }'
}

gpg_kill_if_updated() {
  local gpg_before="$1"
  local gpg_after
  gpg_after=$(gpg_version)
  if [[ -n "$gpg_before" && "$gpg_before" != "$gpg_after" ]]; then
    echo "gnupg updated ($gpg_before -> $gpg_after); running gpgk"
    gpgk
  fi
}

run_with_gpgk() {
  local gpg_before gpg_status
  gpg_before=$(gpg_version)
  "$@"
  gpg_status=$?
  gpg_kill_if_updated "$gpg_before"
  return $gpg_status
}
