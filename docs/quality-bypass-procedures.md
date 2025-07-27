# Quality Check Bypass Procedures

## Emergency Override for Critical Production Fixes

### When to Use Emergency Bypass

Use **ONLY** for:
- Critical production outages
- Security vulnerability fixes  
- Data loss prevention
- Customer-impacting issues requiring immediate deployment

### Emergency Bypass Commands

#### Skip All Pre-commit Hooks
```bash
git commit --no-verify -m "emergency: critical production fix - [brief description]"
```

#### Skip Specific Hooks
```bash
# Skip slow E2E tests but keep format checks
SKIP=critical-e2e-tests git commit -m "hotfix: urgent API response fix"

# Skip type checking for quick fixes
SKIP=mypy git commit -m "hotfix: configuration update"

# Skip security scan for dependency updates
SKIP=bandit git commit -m "deps: update critical security dependency"
```

### Emergency Workflow

1. **Identify criticality**:
   - Is this blocking production?
   - Are customers affected?
   - Is data at risk?

2. **Document the bypass**:
   ```bash
   git commit --no-verify -m "emergency: [ISSUE-ID] brief description of critical fix"
   ```

3. **Create immediate follow-up**:
   - Open GitHub issue for quality remediation
   - Schedule quality fix within 24 hours
   - Add tech debt tracking

4. **Post-emergency cleanup**:
   ```bash
   # Fix quality issues in follow-up commit
   git add .
   git commit -m "quality: fix issues from emergency bypass [ISSUE-ID]"
   ```

### Team Notification

After using emergency bypass:

1. **Slack notification**: Alert #dev-team channel
2. **GitHub issue**: Create quality remediation ticket
3. **Documentation**: Update emergency log

### Quality Remediation Checklist

After emergency bypass, address:
- [ ] Run full pre-commit hooks: `pre-commit run --all-files`
- [ ] Fix any JSON response format issues
- [ ] Resolve MCP protocol compliance errors
- [ ] Update type annotations
- [ ] Run security scan
- [ ] Execute E2E tests against production server
- [ ] Update documentation if needed
- [ ] Close emergency bypass issue

### Approval Matrix

| Severity | Who Can Bypass | Notification Required |
|----------|---------------|----------------------|
| P0 - Production Down | Any team member | Immediate Slack + GitHub issue |
| P1 - Customer Impact | Tech Lead approval | Slack within 1 hour |
| P2 - Minor Issues | **NO BYPASS** - Fix quality issues first |

### Monitoring and Metrics

Track emergency bypasses:
- Frequency per month (target: <2)
- Time to quality remediation (target: <24 hours)
- Root cause analysis for patterns

### Examples

#### ✅ Valid Emergency Bypass
```bash
# Production API returning 500 errors
git commit --no-verify -m "emergency: fix null pointer in story creation API"
```

#### ❌ Invalid Emergency Bypass  
```bash
# Minor formatting issue - NOT an emergency
git commit --no-verify -m "fix: update variable name formatting"
```

### Recovery Commands

If emergency bypass causes issues:

```bash
# Revert the emergency commit
git revert HEAD --no-edit

# Fix properly with quality checks
git add .
git commit -m "fix: proper resolution with quality checks"
```

### Contact Information

For emergency bypass questions:
- **Tech Lead**: [Contact info]
- **DevOps**: [Contact info] 
- **Emergency escalation**: [Contact info]

---

**Remember**: Emergency bypass is a last resort. Most issues can be resolved by fixing quality check failures.