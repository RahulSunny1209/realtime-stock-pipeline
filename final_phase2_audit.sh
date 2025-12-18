#!/bin/bash
echo "╔════════════════════════════════════════════════════════════╗"
echo "║            PHASE 2 - COMPREHENSIVE FINAL AUDIT             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 1. PROJECT STRUCTURE
echo "📁 Project Structure:"
[ -d src/producer ] && echo "   ✅ Producer directory" || echo "   ❌ Missing"
[ -d src/consumer ] && echo "   ✅ Consumer directory" || echo "   ❌ Missing"
[ -d src/utils ] && echo "   ✅ Utils directory" || echo "   ❌ Missing"
[ -d config ] && echo "   ✅ Config directory" || echo "   ❌ Missing"
[ -d logs ] && echo "   ✅ Logs directory" || echo "   ❌ Missing"
echo ""

# 2. CRITICAL FILES
echo "📄 Critical Files:"
[ -f docker-compose.yml ] && echo "   ✅ docker-compose.yml" || echo "   ❌ Missing"
[ -f requirements.txt ] && echo "   ✅ requirements.txt" || echo "   ❌ Missing"
[ -f .env ] && echo "   ✅ .env" || echo "   ❌ Missing"
[ -f .gitignore ] && echo "   ✅ .gitignore" || echo "   ❌ Missing"
[ -f README.md ] && echo "   ✅ README.md" || echo "   ❌ Missing"
echo ""

# 3. PYTHON FILES
echo "🐍 Python Files:"
[ -f src/producer/stock_producer.py ] && echo "   ✅ stock_producer.py" || echo "   ❌ Missing"
[ -f src/consumer/stock_consumer.py ] && echo "   ✅ stock_consumer.py" || echo "   ❌ Missing"
[ -f src/utils/logger.py ] && echo "   ✅ logger.py" || echo "   ❌ Missing"
[ -f config/kafka_config.py ] && echo "   ✅ kafka_config.py" || echo "   ❌ Missing"
echo ""

# 4. SECURITY CHECK
echo "🔐 Security:"
grep -q "^\.env$" .gitignore && echo "   ✅ .env in .gitignore" || echo "   ⚠️  .env NOT in .gitignore!"
! grep -q "POLYGON_API_KEY = \"" src/producer/stock_producer.py && echo "   ✅ No hardcoded API key" || echo "   ⚠️  Hardcoded key found!"
echo ""

# 5. DOCKER STATUS
echo "🐳 Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -4
echo ""

# 6. KAFKA HEALTH
echo "📡 Kafka Health:"
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list 2>/dev/null | grep "stock-prices" && echo "   ✅ Topic 'stock-prices' exists" || echo "   ❌ Topic missing"
docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1 && echo "   ✅ Kafka broker responsive" || echo "   ❌ Broker not responding"
echo ""

# 7. GIT STATUS
echo "📦 Git Repository:"
echo "   Branch: $(git branch --show-current)"
echo "   Commits: $(git rev-list --count HEAD)"
echo "   Last commit: $(git log -1 --pretty=format:'%h - %s' | head -c 60)..."
echo "   Uncommitted changes: $(git status --porcelain | wc -l | tr -d ' ')"
echo ""

# 8. PYTHON ENVIRONMENT
echo "�� Python Environment:"
echo "   Virtual env active: $([ -n "$VIRTUAL_ENV" ] && echo 'YES' || echo 'NO')"
echo "   Python version: $(python --version)"
echo "   Packages installed: $(pip list | wc -l)"
echo ""

# 9. LOGS CHECK
echo "📝 Logs:"
[ -f logs/producer.log ] && echo "   ✅ Producer logs exist ($(wc -l < logs/producer.log) lines)" || echo "   ⚠️  No producer logs"
[ -f logs/consumer.log ] && echo "   ✅ Consumer logs exist ($(wc -l < logs/consumer.log) lines)" || echo "   ⚠️  No consumer logs"
echo ""

# 10. DOCUMENTATION
echo "📚 Documentation:"
[ -f docs/medium-posts/phase2-kafka-producer.md ] && echo "   ✅ Blog post #2 outline" || echo "   ❌ Blog outline missing"
[ -f docs/architecture.md ] && echo "   ✅ Architecture docs" || echo "   ⚠️  Architecture docs missing"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    AUDIT COMPLETE                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# FINAL DECISION
ISSUES=0

# Critical checks
[ ! -f .env ] && ((ISSUES++))
[ ! -f src/producer/stock_producer.py ] && ((ISSUES++))
! docker ps | grep -q kafka && ((ISSUES++))
! grep -q "^\.env$" .gitignore && ((ISSUES++))

if [ $ISSUES -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED - PHASE 2 COMPLETE"
    echo "🚀 READY TO PROCEED TO PHASE 3: APACHE SPARK"
    echo ""
    echo "Phase 3 will cover:"
    echo "   1. PySpark installation & configuration"
    echo "   2. Spark Structured Streaming setup"
    echo "   3. Consuming from Kafka with Spark"
    echo "   4. Window functions & aggregations"
    echo "   5. Moving averages calculation"
    echo "   6. Technical indicators"
else
    echo "⚠️  FOUND $ISSUES CRITICAL ISSUES"
    echo "Please resolve before proceeding to Phase 3"
fi
