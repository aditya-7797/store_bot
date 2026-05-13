# Incident Postmortem Template

**Use this template after any production issue is resolved.**

---

## Header

| Field | Value |
|-------|-------|
| **Incident ID** | INC-2026-###  |
| **Date/Time** | YYYY-MM-DD HH:MM UTC |
| **Duration** | X hours, Y minutes |
| **Severity** | Critical / High / Medium / Low |
| **Author** | Name |
| **Reviewed By** | Manager/Lead |
| **Date Published** | YYYY-MM-DD |

---

## 1. Executive Summary

One sentence describing what happened.

Example: *"Database became locked due to concurrent write attempts, causing 45 minutes of service unavailability and 12 failed transactions."*

---

## 2. Timeline

| Time (UTC) | Event | Owner |
|-----------|-------|-------|
| 14:30 | User reported "stock not updating" | Store Mgr |
| 14:32 | Escalated to Backend Dev | Ops |
| 14:35 | Root cause identified: lock on products table | Dev |
| 14:45 | Fix deployed: connection pooling enabled | Dev |
| 14:50 | System recovered, verified no data loss | Dev |

---

## 3. Impact

### What was affected:
- [ ] Inventory operations (specific products/regions?)
- [ ] Customer analytics (RFM updated? Forecasts?)
- [ ] API (which endpoints? how many requests failed?)
- [ ] User experience (dashboard down? slow?)

### Metrics:
- **Users impacted:** X
- **Transactions lost:** Y
- **Revenue impact:** ₹Z (if applicable)
- **Data integrity:** ✅ No loss / ⚠️ Partial / ❌ Significant

---

## 4. Root Cause Analysis

### Primary Cause
Describe the technical root cause (not symptom).

Example: *"Multiple concurrent POST /api/inventory/update requests overwhelmed SQLite write lock mechanism. SQLite allows only one writer; queued writes timed out after 5 seconds."*

### Why It Happened
Context that allowed the issue to occur.

Examples:
- New high-volume testing started without warning
- Recent code change increased request frequency
- System was never load-tested above X QPS
- Missing guard rails (e.g., rate limits)

### Contributing Factors
[ ] Inadequate monitoring  
[ ] No runbook for this scenario  
[ ] Insufficient logging  
[ ] Lack of rate limiting  
[ ] Single point of failure  
[ ] Other: ___

---

## 5. Lessons Learned

### What Went Well
- Team responded quickly
- Communication was clear
- Escalation path worked

### What Could Be Better
1. **Slow diagnosis**
   - Root cause took 3 minutes to identify
   - Action: Add query-level logging to identify lock contention
2. **Lack of automation**
   - Manual fix required; no auto-remediation available
   - Action: Implement connection pool auto-restart on lock timeout
3. **Preventable**
   - Load testing would have caught this
   - Action: Add load test suite to CI/CD

---

## 6. Corrective Actions

| Action | Priority | Owner | Due Date | Status |
|--------|----------|-------|----------|--------|
| Enable connection pooling in SQLite config | High | Backend Dev | 1 week | ✅ Done |
| Add query-level locking metrics to monitoring | High | DevOps | 1 week | 📋 Planned |
| Implement automatic connection reset on timeout | Medium | Backend Dev | 2 weeks | 📋 Planned |
| Load test to 100 QPS before next release | Medium | QA | 2 weeks | 📋 Planned |
| Document SQLite concurrency limits in runbook | Low | Ops | 1 week | ✅ Done |

---

## 7. Prevention

### Short-term (This Week)
1. Add monitoring alert: "Database lock duration > 10s"
2. Add runbook: "How to handle database lock"
3. Train Ops team on manual database recovery

### Medium-term (This Month)
1. Migrate to PostgreSQL (supports true concurrency)
   - Alternative: Use connection pooling library (pgbouncer-like)
2. Implement circuit breaker: fail gracefully if > N lock timeouts in 60s
3. Add load test suite to CI/CD

### Long-term (This Quarter)
1. Architecture review: identify other single-points-of-failure
2. Implement proper queue + worker architecture for async operations
3. Set SLA for recovery time and monitor compliance

---

## 8. References

### Related Issues
- Slack thread: #incident-channel, May 12 2:30 PM
- GitHub issue: #123
- Previous similar incident: INC-2026-045

### Documentation to Update
- [ ] TROUBLESHOOTING_GUIDES.md (add section: "Database locked")
- [ ] SOP_INVENTORY_RECONCILIATION.md (add lock recovery steps)
- [ ] ONBOARDING_GUIDE.md (add "what to do if system is slow")
- [ ] Runbook for Backend Team (add debugging steps)

### Monitoring/Alerting
- Alert added: `database_lock_duration_seconds > 10`
- Dashboard added: Real-time lock wait times

---

## 9. Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Incident Owner | ___ | ___ | ___ |
| Engineering Lead | ___ | ___ | ___ |
| Operations Lead | ___ | ___ | ___ |

---

## Appendix: Debugging Details

### Logs
```
[14:35] ERROR: database is locked (query: UPDATE products SET stock=10 WHERE name='milk')
[14:36] INFO: Lock timeout after 5s
[14:37] ERROR: 12 transactions rolled back
[14:45] INFO: Connection pool enabled, retrying failed transactions
[14:50] INFO: All transactions succeeded on retry
```

### Commands Used for Recovery
```bash
# Identify lock holder
lsof | grep inventory.db

# Kill stuck process
pkill -f "old_backend.py"

# Restart with new config
python run_backend.py --use-connection-pool
```

### Data Integrity Check
```bash
# Verify no duplicate transactions
sqlite3 inventory.db "SELECT transaction_id, COUNT(*) FROM sales GROUP BY transaction_id HAVING COUNT(*) > 1;"
# Result: (empty = no duplicates ✓)

# Verify stock matches transactions
# (custom audit query here)
```

---

## Future Postmortem Template Improvements
- Add "Customer Impact" section with actual complaints received
- Add "Communication Timeline" (what was told to customers when)
- Add "Financial Impact" calculation
- Add "Process Change" section (e.g., new approval needed before deployments)
