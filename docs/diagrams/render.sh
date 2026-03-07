#!/usr/bin/env bash
# Render all PlantUML diagrams to SVG.
# Requires PlantUML on PATH (or set PLANTUML_JAR below).
#
# Usage:
#   bash docs/diagrams/render.sh
#
# On Windows (Git Bash / PowerShell):
#   bash docs/diagrams/render.sh
#   -- or --
#   java -jar plantuml.jar -tsvg docs/diagrams/*.puml
#
# Install PlantUML:
#   macOS:  brew install plantuml
#   Ubuntu: sudo apt install plantuml
#   Windows: download plantuml.jar from https://plantuml.com/download

set -euo pipefail

DIAGRAMS_DIR="$(cd "$(dirname "$0")" && pwd)"

if command -v plantuml &>/dev/null; then
  PLANTUML="plantuml"
elif [ -f "$DIAGRAMS_DIR/plantuml.jar" ]; then
  PLANTUML="java -jar $DIAGRAMS_DIR/plantuml.jar"
elif [ -n "${PLANTUML_JAR:-}" ]; then
  PLANTUML="java -jar $PLANTUML_JAR"
else
  echo "Error: plantuml not found. Place plantuml.jar in docs/diagrams/ or install plantuml." >&2
  exit 1
fi

echo "Rendering diagrams in $DIAGRAMS_DIR ..."
$PLANTUML -tsvg \
  "$DIAGRAMS_DIR/context.puml" \
  "$DIAGRAMS_DIR/building-blocks.puml" \
  "$DIAGRAMS_DIR/runtime.puml" \
  "$DIAGRAMS_DIR/login.puml" \
  "$DIAGRAMS_DIR/register.puml" \
  "$DIAGRAMS_DIR/search-matrix.puml" \
  "$DIAGRAMS_DIR/create-matrix.puml" \
  "$DIAGRAMS_DIR/save-simulation.puml" \
  "$DIAGRAMS_DIR/open-simulation.puml" \
  "$DIAGRAMS_DIR/export-simulation.puml" \
  "$DIAGRAMS_DIR/import-simulation.puml" \
  "$DIAGRAMS_DIR/er.puml"
echo "Done. SVG files written to $DIAGRAMS_DIR"
