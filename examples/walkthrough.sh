#!/usr/bin/env bash
# A tour of the datakyt API with curl and jq.
#
#   docker compose up -d
#   ADMIN_PASSWORD=<password printed by `docker compose logs app`> examples/walkthrough.sh
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:?set ADMIN_PASSWORD}"

step() { printf '\n== %s\n' "$*"; }

step "Log in and get a bearer token"
TOKEN="$(curl -fsS -X POST "$BASE_URL/auth/login" \
  --data-urlencode "username=$ADMIN_EMAIL" --data-urlencode "password=$ADMIN_PASSWORD" |
  jq -r .access_token)"
auth=(-H "Authorization: Bearer $TOKEN")
json=(-H "Content-Type: application/json")

step "Create an office, a project, an equipment type and an employee"
OFFICE="$(curl -fsS "${auth[@]}" "${json[@]}" -d '{"city": "Odesa"}' "$BASE_URL/offices" | jq .id)"
PROJECT="$(curl -fsS "${auth[@]}" "${json[@]}" -d '{"name": "Walkthrough"}' "$BASE_URL/projects" | jq .id)"
TYPE="$(curl -fsS "${auth[@]}" "${json[@]}" -d '{"name": "Tablet"}' "$BASE_URL/types/equipment" | jq .id)"
EMPLOYEE="$(curl -fsS "${auth[@]}" "${json[@]}" "$BASE_URL/employees" -d "{
  \"full_name\": \"Taras Rudenko\", \"email\": \"taras.rudenko@example.com\",
  \"project_id\": $PROJECT, \"office_id\": $OFFICE}" | jq .id)"

step "Register a piece of equipment"
ITEM="$(curl -fsS "${auth[@]}" "${json[@]}" "$BASE_URL/equipment" -d "{
  \"inventory_number\": \"EQ-WALK-1\", \"name\": \"iPad Air\", \"serial_number\": \"DMPX1\",
  \"warranty_months\": 12, \"cost\": \"699.00\", \"purchase_date\": \"2026-09-01\",
  \"equipment_type_id\": $TYPE, \"office_id\": $OFFICE}" | jq .id)"
curl -fsS "${auth[@]}" "$BASE_URL/equipment/$ITEM" | jq '{inventory_number, status}'

step "Issue it to the employee, then list what they hold"
curl -fsS "${auth[@]}" "${json[@]}" -d "{\"employee_id\": $EMPLOYEE}" \
  "$BASE_URL/equipment/$ITEM/issue" | jq .
curl -fsS "${auth[@]}" "$BASE_URL/reports/employee/$EMPLOYEE" | jq .

step "Download a QR label and the inventory report as XLSX"
curl -fsS "${auth[@]}" -o label.png "$BASE_URL/equipment/$ITEM/label.png"
curl -fsS "${auth[@]}" -o inventory.xlsx "$BASE_URL/reports/inventory?format=xlsx"
ls -l label.png inventory.xlsx

step "Return the item for repair"
curl -fsS "${auth[@]}" "${json[@]}" -d '{"status": "in_repair"}' \
  "$BASE_URL/equipment/$ITEM/return" | jq .

step "Dry-run an import: Kyiv already exists in the demo data, so row 1 is reported"
printf 'city\nKyiv\n\n' > offices.csv
curl -fsS "${auth[@]}" -F "file=@offices.csv" "$BASE_URL/import/offices?dry_run=true" | jq .
