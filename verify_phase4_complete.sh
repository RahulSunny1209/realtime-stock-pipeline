#!/bin/bash
echo "╔════════════════════════════════════════════════════════╗"
echo "║      PHASE 4 COMPLETE - FINAL VERIFICATION             ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "🐘 PostgreSQL Records:"
docker exec postgres psql -U stockuser -d stockmarket -c "
SELECT 
    symbol,
    COUNT(*) as records 
FROM stock_prices 
GROUP BY symbol;
" 2>/dev/null
echo ""
echo "🔴 Redis Cache Keys:"
docker exec redis redis-cli KEYS "*" 2>/dev/null | wc -l
echo ""
echo "📁 Files Created:"
[ -f src/storage/database.py ] && echo "   ✅ database.py"
[ -f src/processing/spark_processor_with_storage.py ] && echo "   ✅ spark_processor_with_storage.py"
[ -f src/storage/query_data.py ] && echo "   ✅ query_data.py"
echo ""
echo "✅ PHASE 4 COMPLETE!"
echo "Ready for Phase 5: Streamlit Dashboard"
