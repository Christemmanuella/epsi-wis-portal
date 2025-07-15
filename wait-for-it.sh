#!/bin/sh
# wait-for-it.sh

set -e

# Récupère l'hôte et le port à partir du premier argument (format host:port)
host_port="$1"
shift

# Extrait l'hôte et le port
host=$(echo "$host_port" | cut -d':' -f1)
port=$(echo "$host_port" | cut -d':' -f2)

# Le reste des arguments est la commande à exécuter (ignorant "--" si présent)
while [ "$1" = "--" ]; do shift; done
cmd="$@"

echo "Starting wait-for-it.sh for $host:$port"
until nc -z "$host" "$port"; do
  echo "Waiting for $host:$port..."
  sleep 1
done

echo "$host:$port is available - executing command: $cmd"
exec $cmd