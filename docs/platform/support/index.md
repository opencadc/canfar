# Getting Help and Support

!!! abstract "🎯 Support Resources Overview"
    **Find the help you need:**
    
    - **Self-service**: Documentation, troubleshooting guides, and FAQs
    - **Community**: User discussions, office hours, and peer assistance
    - **Direct support**: Help from CANFAR platform specialists
    - **Emergency**: Rapid response for critical incidents

The CANFAR Science Platform offers several ways to get assistance. Start with self-service resources, then move to community channels or direct support as needed.

## 🚀 Quick Start for Support

### New to CANFAR?

- **[Get Started Guide](../get-started.md)**: 10-minute overview
- **[First Login](../permissions.md)**: Account activation and access
- **[Choose Your Interface](../sessions/index.md)**: Pick the right session type

### Having Problems?

- **[FAQ](faq.md)**: Quick answers to common questions
- **[Troubleshooting](#troubleshooting)**: Diagnostic steps for common issues
- **[Contact Support](#contact-support)**: Reach the CANFAR team for help

## 📚 Self-Help Resources

- **Documentation search**: Use the search box or browse by topic
- **[Concepts](../concepts.md)**: Platform architecture and terminology
- **[Storage](../storage/index.md)**: Managing data effectively
- **[Containers](../containers/index.md)**: Using and building software environments
- **[Interactive Sessions](../sessions/index.md)**: Jupyter, Desktop, CARTA, Firefly
- **[Batch Jobs](../sessions/batch.md)**: Automated and large-scale processing

## 🔧 Troubleshooting

### Quick Checks

1. Confirm there are no current maintenance announcements
2. Try Chrome or Firefox and clear the browser cache
3. Use a private/incognito window to rule out extensions
4. Verify your network connection is stable

### Frequent Issues

#### Session won't start

- Lower memory or CPU requests and retry
- Try a different container image or launch time
- Ensure your account has the required group memberships

#### Cannot access files

```bash
# Check locations and permissions
ls /arc/home/[user]/
ls /arc/projects/[project]/
ls -la /arc/projects/[project]/
getfacl /arc/projects/[project]/
```

- Confirm the path and project name
- Verify you belong to the correct project group
- Contact the project administrator if permissions are missing

#### Performance feels slow

- Monitor resource usage with `htop`
- Close unused applications and tabs
- Use `/scratch/` for temporary, high-I/O workloads
- Submit a support request if performance remains degraded

#### Browser quirks

- Stick to Chrome or Firefox and keep them updated
- Enable JavaScript and cookies for `canfar.net`
- Disable ad blockers or privacy extensions for the site

### Gather Information Before Asking for Help

Run these commands to capture context for a support request:

```bash
# Platform status
canfar info [session-id]
canfar stats

# Session details
echo $USER
groups
env | grep -E "(CANFAR|SKAHA)"
```

## 📧 Contact Support

### When to Reach Out

Email [support@canfar.net](mailto:support@canfar.net) when you encounter:

- **Account issues**: Login failures, certificate problems, group membership
- **Technical problems**: Persistent errors, failed sessions, system outages
- **Data concerns**: Missing files, data corruption, recovery requests
- **Resource changes**: Requests for additional storage, CPU, or RAM
- **Software help**: Complex installations or container customization

### What to Include

Provide clear, specific details to speed up triage:

- **Subject**: Short summary of the problem
- **Contact**: CANFAR username and email
- **Timeline**: Date and time (with timezone) when the issue occurred
- **Environment**: Session type, container, operating system, browser
- **Steps to reproduce**: Numbered list of actions leading to the issue
- **Observed vs expected**: What happened and what you expected
- **Error output**: Copy exact error text and attach screenshots when available
- **What you tried**: Mention any workarounds attempted

### Expected Response Times

| Priority | Response Time | Examples |
|----------|---------------|----------|
| **Critical** | Same day | System outages, data loss, security issues |
| **High** | 1–2 business days | Session failures, access problems |
| **Normal** | 2–3 business days | General questions, documentation requests |
| **Low** | 3–5 business days | Feature requests, enhancement suggestions |

### Escalation

If a ticket is not progressing within the expected timeframe:

1. Reply to the original email and add "URGENT" to the subject
2. Share any new details or screenshots gathered since the initial report
3. For emergencies, follow the contacts listed in [🚨 Emergency Contacts](#emergency-contacts)

## 👥 Community Support

### Discord

Join the [CANFAR Discord](https://discord.gg/vcCQ8QBvBa) for real-time conversations with other users and staff.

- Search existing threads before posting
- Use the channel that matches your topic
- Share concise questions and relevant context
- Never publish sensitive data or credentials

### GitHub

Use [GitHub Issues](https://github.com/opencadc/canfar/issues) to track bugs, suggest enhancements, or contribute documentation updates.

- Reference related documentation pages or example workflows
- Tag issues appropriately (e.g., `bug`, `documentation`, `feature-request`)
- Follow up on discussions to confirm fixes or add clarifications

## 🐛 Helpful Bug Reports

### Before Filing

1. Search the documentation and [FAQ](faq.md) for related answers
2. Look for existing issues on GitHub to avoid duplicates
3. Ask quick questions on Discord if you are unsure whether something is a bug

### What Maintainers Need

- Clear, descriptive title
- Environment details (OS, browser, session type, container)
- Steps to reproduce, numbered and complete
- Expected result versus what actually happened
- Complete error output and supporting screenshots or logs
- Notes on any temporary workarounds you discovered

This template can help structure a report:

```markdown
## Bug Description
[Short summary]

## Environment
- OS: [...]
- Browser: [...]
- Session Type: [...]
- Container: [...]

## Steps to Reproduce
1. [...]
2. [...]

## Expected Behavior
[...]

## Actual Behavior
[...]

## Error Messages
```text
[Paste exact text]
```

## Screenshots
If applicable, add screenshots to help explain the problem.

## Additional Context
[Anything else that helps]
```

After submitting, monitor the issue for follow-up questions, provide additional details promptly, and test proposed fixes when available.

## 🚨 Emergency Contacts

### System Outages

- Planned maintenance notices go out at least 48 hours in advance via email and Discord
- For unexpected outages, email [support@canfar.net](mailto:support@canfar.net) and request a status update

### Critical Data Issues

1. Stop affected jobs or sessions immediately
2. Document what happened and when
3. Email [support@canfar.net](mailto:support@canfar.net) with **URGENT** in the subject
4. Preserve files and logs so recovery is possible

Daily snapshots of `/arc/` storage are retained for 30 days; support can coordinate point-in-time recovery when necessary.

### Security Incidents

1. Revoke and reissue credentials right away
2. Report the incident to [support@canfar.net](mailto:support@canfar.net)
3. Describe what you observed, including timestamps and IP addresses if known
4. Follow instructions from the security team before resuming activity

## 📝 Contributing

Documentation is community-driven. If you spot something to improve:

1. Browse the source on [GitHub](https://github.com/opencadc/canfar)
2. Follow the contribution guidelines in `CONTRIBUTING.md`
3. Submit a pull request or open an issue describing the change

For help getting started, ask in Discord or email [support@canfar.net](mailto:support@canfar.net).
