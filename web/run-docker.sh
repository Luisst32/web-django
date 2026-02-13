#!/bin/bash

# Script para ejecutar Docker con WebSockets usando Daphne

echo "🐳 Limpiando contenedores anteriores..."
docker compose down -v

echo "🔨 Construyendo imagen Docker..."
docker compose build

echo "🚀 Iniciando servicios..."
docker compose up -d

echo ""
echo "✅ Servicios iniciados correctamente"
echo ""
echo "📊 Estado de contenedores:"
docker compose ps
echo ""
echo "🌐 Aplicación disponible en: http://localhost:8000"
echo "📝 Para ver logs: docker compose logs -f web"
echo "🛑 Para detener: docker compose down"
