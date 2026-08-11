#!/bin/sh
# Send en .gcode-fil til printeren over FTPS.
# Bruk: scripts/send.sh fil.gcode
# Access code hentes fra $STREK_ACCESS_CODE eller scripts/.env (gitignored).
# Krever lftp (brew install lftp): Bambu-FTP-serveren krever TLS session
# reuse på dataforbindelsen — curl (både LibreSSL og OpenSSL) og Pythons
# ftplib feiler med "522 session reuse required"; lftp/GnuTLS fungerer.
set -eu

PRINTER_IP="${STREK_PRINTER_IP:-192.168.1.15}"

command -v lftp >/dev/null || { echo "Mangler lftp: brew install lftp" >&2; exit 1; }

[ -f "$(dirname "$0")/.env" ] && . "$(dirname "$0")/.env"

if [ -z "${STREK_ACCESS_CODE:-}" ]; then
    echo "Sett STREK_ACCESS_CODE (fra printerskjermen), f.eks. i scripts/.env:" >&2
    echo "  STREK_ACCESS_CODE=xxxxxxxx" >&2
    exit 1
fi

lftp -u "bblp,$STREK_ACCESS_CODE" \
    -e "set ssl:verify-certificate no; put \"$1\"; bye" \
    "ftps://$PRINTER_IP:990"
echo "Sendt: $(basename "$1") → $PRINTER_IP (start fra printerskjermen)"
