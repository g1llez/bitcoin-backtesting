#!/bin/bash

# Script pour ajouter les données d'efficacité de la S19 Pro
# ID de la machine S19 Pro (à ajuster si nécessaire)
MACHINE_ID=1

# Données d'efficacité de la S19 Pro
declare -a data=(
    '{"machine_id": 1, "effective_hashrate": 104.10, "power_consumption": 2849}'
    '{"machine_id": 1, "effective_hashrate": 107.00, "power_consumption": 2957}'
    '{"machine_id": 1, "effective_hashrate": 110.00, "power_consumption": 3028}'
    '{"machine_id": 1, "effective_hashrate": 113.80, "power_consumption": 3180}'
    '{"machine_id": 1, "effective_hashrate": 114.60, "power_consumption": 3240}'
    '{"machine_id": 1, "effective_hashrate": 119.40, "power_consumption": 3379}'
    '{"machine_id": 1, "effective_hashrate": 120.20, "power_consumption": 3388}'
    '{"machine_id": 1, "effective_hashrate": 121.50, "power_consumption": 3492}'
    '{"machine_id": 1, "effective_hashrate": 122.37, "power_consumption": 3555}'
    '{"machine_id": 1, "effective_hashrate": 122.40, "power_consumption": 3560}'
    '{"machine_id": 1, "effective_hashrate": 123.00, "power_consumption": 3593}'
    '{"machine_id": 1, "effective_hashrate": 125.50, "power_consumption": 3680}'
    '{"machine_id": 1, "effective_hashrate": 125.80, "power_consumption": 3700}'
    '{"machine_id": 1, "effective_hashrate": 125.70, "power_consumption": 3705}'
    '{"machine_id": 1, "effective_hashrate": 127.73, "power_consumption": 3780}'
    '{"machine_id": 1, "effective_hashrate": 130.20, "power_consumption": 3892}'
    '{"machine_id": 1, "effective_hashrate": 133.20, "power_consumption": 4008}'
    '{"machine_id": 1, "effective_hashrate": 134.37, "power_consumption": 4080}'
    '{"machine_id": 1, "effective_hashrate": 136.70, "power_consumption": 4180}'
)

echo "Ajout des données d'efficacité pour la S19 Pro (ID: $MACHINE_ID)..."

for data_point in "${data[@]}"; do
    echo "Ajout: $data_point"
    curl -X POST "http://localhost:8000/api/v1/efficiency/curves" \
        -H "Content-Type: application/json" \
        -d "$data_point"
    echo ""
    sleep 0.5
done

echo "Données d'efficacité ajoutées avec succès!" 