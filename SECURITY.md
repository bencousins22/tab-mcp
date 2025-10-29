# Security Policy - Tabcorp MCP Server

## 🔐 Overview

This document outlines security best practices, credential management, vulnerability reporting, and security audit procedures for the Tabcorp MCP Server.

---

## 🛡️ Security Best Practices

### Credential Management

#### DO ✅

- **Use environment variables** for all sensitive data
- **Rotate credentials** every 90 days minimum
- **Use strong passwords** (minimum 16 characters, mixed case, numbers, symbols)
- **Enable 2FA** on all accounts (Tabcorp, GitHub, Smithery)
- **Store secrets securely** using platform secret managers:
  - Local: `.env` files (gitignored)
  - Smithery: Environment variables in dashboard
  - GitHub: Repository secrets
- **Audit access logs** monthly for suspicious activity
- **Use least privilege** principle for all credentials
- **Document security incidents** and lessons learned

#### DON'T ❌

- **Never commit secrets** to git repositories
- **Never log credentials** in application logs
- **Never display credentials** in UI or responses
- **Never share credentials** via email, Slack, or insecure channels
- **Never reuse passwords** across different services
- **Never hard-code credentials** in source code
- **Never store credentials** in unencrypted files

---

## 🔑 Secrets Management

### Required Credentials

| Credential | Type | Sensitivity | Rotation Period |
|------------|------|-------------|------------------|
| `TAB_CLIENT_ID` | OAuth Client ID | Medium | 180 days |
| `TAB_CLIENT_SECRET` | OAuth Secret | **Critical** | 90 days |
| `TAB_USERNAME` | Account Username | High | When compromised |
| `TAB_PASSWORD` | Account Password | **Critical** | 90 days |

### Setting Up Secrets

#### Local Development

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your actual credentials
# Use a secure editor, don't echo to terminal
vim .env  # or nano, code, etc.

# 3. Verify .env is gitignored
grep -q '.env' .gitignore && echo "✅ Safe" || echo "⚠️ WARNING: .env not gitignored!"

# 4. Verify .env has correct permissions (readable only by you)
chmod 600 .env
ls -l .env  # Should show -rw-------
```

#### Smithery Deployment

1. Navigate to Smithery Dashboard: https://smithery.ai
2. Go to your server: @bencousins22/tab-mcp
3. Click **"Settings"** → **"Environment Variables"**
4. Add each variable:
   - Click **"Add Variable"**
   - Enter variable name (e.g., `TAB_CLIENT_ID`)
   - Enter value (paste from secure source)
   - Click **"Save"**
5. Verify all 4 required variables are set
6. Click **"Deploy"** to apply changes

#### GitHub Actions (CI/CD)

1. Go to repository: https://github.com/bencousins22/tab-mcp
2. Click **"Settings"** → **"Secrets and variables"** → **"Actions"**
3. Click **"New repository secret"**
4. Add each secret:
   - Name: `TAB_CLIENT_ID`
   - Value: (paste from secure source)
   - Click **"Add secret"**
5. Repeat for all 4 credentials
6. Verify secrets appear in the list (values are hidden)

---

## 🔍 Security Audit Checklist

### Monthly Security Review

- [ ] Review access logs for unusual activity
- [ ] Verify all secrets are still valid
- [ ] Check for exposed credentials in git history
- [ ] Update dependencies with security patches
- [ ] Review GitHub security advisories
- [ ] Verify 2FA is enabled on all accounts
- [ ] Check Smithery deployment security settings

### Quarterly Security Audit

- [ ] **Rotate all credentials**
- [ ] Run security scan: `bandit -r src/ -ll`
- [ ] Review and update security policies
- [ ] Audit third-party dependencies for vulnerabilities
- [ ] Test disaster recovery procedures
- [ ] Review and update access controls
- [ ] Document any security incidents

### Automated Security Checks

The GitHub Actions workflow includes automated security scanning:

```yaml
# .github/workflows/test.yml includes:
security:
  name: Security Scan
  runs-on: ubuntu-latest
  steps:
    - uses: tj-actions/bandit@v5.5
      with:
        targets: src/
        options: "-r -ll"
```

**What it checks:**
- Hard-coded credentials (prevents accidental commits)
- SQL injection vulnerabilities
- Command injection risks
- Insecure cryptographic practices
- Known security anti-patterns

---

## 🚨 Vulnerability Reporting

### Reporting Security Issues

If you discover a security vulnerability:

#### For Critical Issues (P0)

1. **DO NOT** open a public GitHub issue
2. **DO NOT** disclose publicly until patched
3. Contact maintainers privately:
   - Create a private security advisory on GitHub
   - Or email repository maintainers directly
4. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

#### For Non-Critical Issues (P1-P3)

1. Open a GitHub issue with label "security"
2. Provide detailed description
3. Include steps to reproduce
4. Suggest mitigation if possible

### Response Timeline

| Severity | Response Time | Fix Timeline |
|----------|---------------|---------------|
| Critical (P0) | < 4 hours | < 24 hours |
| High (P1) | < 24 hours | < 7 days |
| Medium (P2) | < 3 days | < 30 days |
| Low (P3) | < 7 days | Next release |

---

## 🔒 Secure Development Practices

### Code Review Requirements

All code changes must:
- ✅ Pass automated security scans
- ✅ Not introduce hard-coded credentials
- ✅ Properly handle sensitive data
- ✅ Include security considerations in review
- ✅ Follow OWASP best practices

### Testing Security

```bash
# Run security scan locally before committing
bandit -r src/ -ll

# Check for secrets in code
git secrets --scan

# Verify .env is not tracked
git status --ignored | grep .env
```

### Dependencies

```bash
# Check for vulnerable dependencies
pip install safety
safety check

# Update dependencies with security patches
uv pip install --upgrade <package>
```

---

## 📋 Compliance

### Data Protection

- **No PII storage**: Server does not store user personal data
- **Credentials in transit**: All API calls use HTTPS
- **Token management**: OAuth tokens are ephemeral and refreshed
- **Logging**: No sensitive data in logs

### Regulatory Considerations

- Comply with Tabcorp API terms of service
- Follow OAuth 2.0 security best practices
- Implement secure token storage and refresh
- Audit all credential access

---

## 🔧 Security Tools

### Recommended Tools

1. **Bandit** - Python security linter
   ```bash
   pip install bandit
   bandit -r src/ -ll
   ```

2. **Safety** - Dependency vulnerability checker
   ```bash
   pip install safety
   safety check
   ```

3. **git-secrets** - Prevent committing secrets
   ```bash
   # Install git-secrets
   brew install git-secrets  # macOS
   apt-get install git-secrets  # Linux
   
   # Set up in repository
   git secrets --install
   git secrets --register-aws
   ```

4. **pre-commit** - Git hooks for security checks
   ```bash
   pip install pre-commit
   pre-commit install
   ```

---

## 📚 Security Resources

### Best Practices

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [Python Security Guide](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)

### Training

- [OWASP Security Training](https://owasp.org/www-project-application-security-curriculum/)
- [GitHub Security Lab](https://securitylab.github.com/)

---

## 📝 Incident Response

### Security Incident Procedure

1. **Detect** - Identify security incident
2. **Contain** - Immediately rotate compromised credentials
3. **Investigate** - Determine scope and impact
4. **Remediate** - Fix vulnerability and deploy patch
5. **Document** - Create post-mortem
6. **Prevent** - Implement safeguards against recurrence

### Credential Compromise Response

If credentials are compromised:

```bash
# 1. Immediately rotate ALL credentials
# - Generate new TAB_CLIENT_SECRET in Tabcorp dashboard
# - Change TAB_PASSWORD in Tabcorp account
# - Update TAB_CLIENT_ID if possible

# 2. Update credentials everywhere
# - Local .env file
# - Smithery environment variables
# - GitHub Actions secrets

# 3. Redeploy to apply new credentials
# - Trigger deployment via Smithery UI
# - Verify new credentials work

# 4. Audit access logs
# - Check Tabcorp API logs for unauthorized access
# - Review GitHub access logs
# - Check Smithery deployment logs

# 5. Document incident
# - Create GitHub issue with "security" and "incident" labels
# - Document timeline, impact, and remediation
# - Update security procedures to prevent recurrence
```

---

## ✅ Security Verification

### Pre-Deployment Security Checklist

Before every deployment:

- [ ] Security scan passes (`bandit -r src/ -ll`)
- [ ] No hard-coded credentials in code
- [ ] All secrets using environment variables
- [ ] `.env` file is gitignored
- [ ] Dependencies have no known vulnerabilities
- [ ] Code review includes security considerations
- [ ] Authentication flow tested
- [ ] Token refresh mechanism validated

### Post-Deployment Security Verification

- [ ] Server responds to health checks
- [ ] Authentication works correctly
- [ ] No credentials in logs
- [ ] HTTPS enforced for all connections
- [ ] Token refresh working as expected

---

## 📞 Security Contacts

**Security Issues**: Create private security advisory on GitHub  
**General Questions**: Open GitHub issue with "security" label  
**Urgent Matters**: Contact repository maintainers directly

---

*Last Updated: 2024-10-29*  
*Version: 1.0.0*  
*Next Review: 2025-01-29*
