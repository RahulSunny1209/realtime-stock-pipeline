#!/bin/bash
echo "╔════════════════════════════════════════════════╗"
echo "║  PHASE 4 - CHECKPOINT 2: Storage Layer        ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "📝 Storage Module:"
[ -f src/storage/database.py ] && echo "   ✅ database.py created" || echo "   ❌ Missing"
echo ""
echo "🐘 PostgreSQL Data:"
docker exec postgres psql -U stockuser -d stockmarket -c "SELECT COUNT(*) as price_records FROM stock_prices;" 2>/dev/null
echo ""
echo "🔴 Redis Cache:"
docker exec redis redis-cli DBSIZE 2>/dev/null
docker exec redis redis-cli KEYS "latest_price:*" 2>/dev/null
echo ""
echo "✅ Ready for Step 3: Spark Integration"
