#!/bin/bash

# Script pour ajouter des données de test d'efficacité
# ID de la machine S19 Pro
MACHINE_ID=1

# Données de test (TH/s, Watt)
declare -a test_data=(
    '{"machine_id": 1, "effective_hashrate": 90.0, "power_consumption": 2500}'
    '{"machine_id": 1, "effective_hashrate": 92.5, "power_consumption": 2550}'
    '{"machine_id": 1, "effective_hashrate": 95.0, "power_consumption": 2600}'
    '{"machine_id": 1, "effective_hashrate": 97.5, "power_consumption": 2650}'
    '{"machine_id": 1, "effective_hashrate": 100.0, "power_consumption": 2700}'
    '{"machine_id": 1, "effective_hashrate": 102.5, "power_consumption": 2750}'
    '{"machine_id": 1, "effective_hashrate": 105.0, "power_consumption": 2800}'
)

echo "Ajout de données de test pour la S19 Pro (ID: $MACHINE_ID)..."

for data_point in "${test_data[@]}"; do
    echo "Ajout: $data_point"
    curl -X POST "http://localhost:8000/api/v1/efficiency/curves" \
        -H "Content-Type: application/json" \
        -d "$data_point"
    echo ""
    sleep 0.5
done

echo "Données de test ajoutées avec succès!"
echo ""
echo "Test du ratio 0.8 maintenant possible:"
curl "http://localhost:8000/api/v1/efficiency/machines/1/ratio/0.8" | jq 