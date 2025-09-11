# Getting Help and Support

!!! abstract "🎯 Support Resources Overview"
    **Find the help you need:**
    
    - **Self-Service**: Documentation, troubleshooting guides, and FAQ resources
    - **Community Support**: User discussions, office hours, and peer assistance
    - **Technical Support**: Direct help from CANFAR platform specialists
    - **Emergency Contacts**: Critical issue resolution and urgent assistance

The CANFAR Science Platform provides multiple channels for getting help, from self-service documentation to direct support. This section guides you to the right resources for your needs.

## 🚀 Quick Start for Support

### New to CANFAR?

- **[Get Started Guide](../get-started.md)**: 10-minute quick start
- **[First Login](../permissions.md)**: Account setup and access
- **[Choose Your Interface](../sessions/index.md)**: Pick the right session type

### Having Problems?

- **[FAQ](faq.md)**: Common questions and solutions
- **[Troubleshooting](#troubleshooting)**: Diagnostic steps for common issues
- **[Contact Support](#contact-support)**: Direct help from CANFAR staff

## 📚 Self-Help Resources

### Documentation

**User Guide Sections:**

- **[Concepts](../concepts.md)**: Understanding the platform architecture
- **[Storage](../storage/index.md)**: Managing your data effectively
- **[Containers](../containers/index.md)**: Using and building software environments
- **[Interactive Sessions](../sessions/index.md)**: Jupyter, Desktop, CARTA
- **[Batch Jobs](../sessions/batch.md)**: Automated and large-scale processing

## 🔧 Troubleshooting

### Quick Diagnostic Steps

When you encounter issues, try these steps first:

1. **Check system status**: Look for maintenance announcements
2. **Try a different browser**: Chrome and Firefox work best
3. **Clear browser cache**: Remove cookies and cached data
4. **Try incognito mode**: Eliminates browser extension conflicts
5. **Check your network**: Ensure stable internet connection

### Common Issues and Solutions

#### Session Won't Start

**Symptoms**: Session creation fails or hangs

**Solutions:**

- Reduce resource requirements (memory/CPU)
- Try during off-peak hours (evenings, weekends)
- Select a different container image
- Check group permissions

#### Can't Access Files

**Symptoms**: Files missing or permission denied

**Solutions:**

```bash
# Check file locations
ls /arc/home/[user]/     # Personal storage
ls /arc/projects/[project]           # Group storage

# Check permissions
ls -la /arc/projects/[project]/
getfacl /arc/projects/[project]/
```

- Verify you're in the correct group
- Check file paths are correct
- Contact group administrator

#### Performance Issues

!!! tip "Advanced: Optimising Performance"
    - Use [Batch Jobs](../sessions/batch.md) for large-scale or automated processing.
    - Monitor session resource usage with [`canfar info [session-id]`](../../cli/cli-help.md#canfar-info).
    - Store temporary files in `/scratch/` for faster I/O.
    - For parallel workloads, see [Distributed Computing](../../client/helpers.md).

**Symptoms**: Slow processing or unresponsive interface

**Solutions:**

- Monitor resource usage with `htop`
- Close unnecessary applications
- Use scratch storage (`/scratch/`) for temporary files
- Consider requesting more resources

#### Browser Compatibility

!!! tip "Advanced: Browser Automation"
    - Use browser profiles/extensions for session isolation.
    - Automate repetitive browser tasks with [Selenium](https://www.selenium.dev/) or [Playwright](https://playwright.dev/).

**Symptoms**: Interface doesn't load or behaves incorrectly

**Solutions:**

- Use Chrome or Firefox (recommended)
- Enable JavaScript and cookies
- Disable ad blockers for canfar.net
- Update browser to latest version

### Diagnostic Commands

!!! example "Gathering Diagnostic Info for Support"
    Use these commands before contacting support to speed up troubleshooting:

Use these commands to gather information for support requests:

```bash
# System information
canfar info [session-id]
canfar stats

# Within session information
echo $USER
groups
env | grep -E "(CANFAR|SKAHA)"
```

### When to Contact Support

Contact [support@canfar.net](mailto:support@canfar.net) for:

- **Account issues**: Access problems, group membership
- **Technical problems**: Persistent errors, system failures
- **Data recovery**: Lost or corrupted files
- **Resource requests**: Increased storage or compute allocations
- **Software installation**: Help with complex software setups

## 📧 Contact Support

### How to Write Effective Support Requests

Include these details in your support email:

**Essential information:**

Example:

```text
Subject: [Brief description of problem]

CANFAR Username: your.email@domain.com
Date/Time of issue: 2024-01-15 14:30 PST
Session type: desktop | notebook | carta | firefly | headless
Container used: skaha/astroml:latest
Browser: Chrome 120.0.6099

Problem description:
[Detailed description of what you were trying to do]

Error messages:
[Copy/paste exact error text]

Steps to reproduce:
1. Login to Science Portal
2. Create desktop session
3. [etc.]

What you've already tried:

- Cleared browser cache
- Tried different browser
- [etc.]

```

**Additional helpful information:**

- Screenshots of error messages
- Session IDs for failed jobs
- File paths for missing data
- Group names for permission issues

### Expected Response Times

| Priority | Response Time | Examples |
|----------|---------------|----------|
| **Critical** | Same day | System outages, data loss, security issues |
| **High** | 1-2 business days | Session failures, access problems |
| **Normal** | 2-3 business days | General questions, documentation requests |
| **Low** | 3-5 business days | Feature requests, enhancement suggestions |

### Support Escalation

If your issue isn't resolved within expected timeframes:

1. **Reply to your original email** with "URGENT" in subject
2. **Provide additional context** if the situation has changed
3. **For emergencies**: Use emergency contacts below

## 👥 Community Support

### Discord Community

!!! tip "Advanced: Community Collaboration"
    - Share workflow examples in Discord.
    - Use Discord threads for project-specific discussions.

Join our Discord server for peer support and community interaction:

- **Quick questions**: Get fast answers from other users
- **Tips and tricks**: Share and learn best practices
- **Collaboration**: Find research partners and collaborators
- **Announcements**: Stay updated on new features and maintenance

**Discord invite**: [Join CANFAR Discord](https://discord.gg/vcCQ8QBvBa)

**Community guidelines:**

- Search previous messages before asking
- Use appropriate channels and threads
- Be respectful and helpful to other users
- Don't share sensitive data or credentials

### GitHub Issues

!!! tip "Advanced: Effective GitHub Contributions"
    - Reference related documentation pages in your issue or pull request.
    - Link to example workflows or scripts.
    - Tag your issue with relevant labels (e.g., `documentation`, `feature-request`).

For bug reports and feature requests, use our GitHub repositories:

- **Platform issues**: Report technical problems
- **Documentation**: Suggest improvements
- **Feature requests**: Propose new capabilities
- **Community contributions**: Submit code and examples

### Community Contributions

!!! tip "Advanced: Share Your Expertise"
    - Submit tutorials or workflow examples to the documentation via GitHub.
    - Answer questions in Discord and GitHub Issues.
    - Report bugs and suggest features to improve the platform for all users.

**Ways to help other users:**

- **Answer questions**: Respond to Discord and community discussions
- **Share tutorials**: Create workflow examples
- **Report bugs**: Help improve platform stability
- **Suggest features**: Propose improvements

## 🐛 Filing Issues and Bug Reports

### Before Filing an Issue

**Check existing resources:**

1. **Search documentation**: Use the search function or browse relevant sections
2. **Check FAQ**: Review [common questions and solutions](faq.md)
3. **Search existing issues**: Look through [GitHub Issues](https://github.com/opencadc/canfar/issues)
4. **Try Discord**: Ask quick questions in the community chat

### What Makes a Good Bug Report

#### ✅ Good Bug Reports Include

- **Clear title**: Concise description of the problem
- **Environment details**: OS, browser, session type, container
- **Reproduction steps**: Exact steps to trigger the issue
- **Expected vs actual**: What should happen vs what actually happens
- **Error messages**: Complete, unedited error text
- **Screenshots**: Visual evidence of the problem
- **Workarounds**: Any temporary solutions you've found

#### ❌ Poor Bug Reports

- Vague descriptions like "it doesn't work"
- Missing reproduction steps
- No environment information
- Screenshots without context
- Duplicate of existing issues

### Creating Effective Issue Reports

**Template for bug reports:**

```markdown
## Bug Description
[Clear, concise description of the bug]

## Environment
- OS: [e.g., macOS 14.1, Windows 11, Ubuntu 24.04]
- Browser: [e.g., Chrome 120.0, Firefox 119.0]
- Session Type: [notebook, desktop, carta, firefly, headless]
- Container: [e.g., skaha/astroml:latest]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [etc.]

## Expected Behavior
[What you expected to happen]

## Actual Behavior
[What actually happened]

## Error Messages

```text
[Copy/paste exact error text]
```

## Screenshots

[If applicable, add screenshots]

## Additional Context

[Any other relevant information]

```markdown

```

### After Reporting

After you submit a bug report:

- **Monitor the issue**: Watch for responses from maintainers
- **Provide additional information**: Be ready to answer follow-up questions
- **Test fixes**: Help test proposed solutions when available
- **Update the issue**: Let us know if the problem is resolved

## 🚨 Emergency Contacts

### System Outages

**Planned maintenance**: Announced 48+ hours in advance via email and Discord

**Unplanned outages:**

- Check status.canfar.net for current status (when available)
- Email [support@canfar.net](mailto:support@canfar.net) if status unclear

### Critical Data Issues

**Data loss or corruption:**

1. **Stop all activity**: Prevent further damage
2. **Document the issue**: Note exactly what happened
3. **Contact support immediately**: Mark email as URGENT
4. **Preserve evidence**: Don't delete or modify files

**Backup and recovery:**

- Daily snapshots of `/arc/` storage
- 30-day retention period
- Point-in-time recovery available
- Contact support for restoration requests

### Security Incidents

**Suspected security breach:**

1. **Change credentials**: Update certificates immediately
2. **Report incident**: Email [support@canfar.net](mailto:support@canfar.net)
3. **Document details**: What you observed and when
4. **Follow instructions**: Wait for security team guidance

**Prevention:**

- Never share your certificates
- Keep software updated
- Report suspicious activity

## 📝 Contributing to Documentation

### How to Contribute

The CANFAR documentation is community-driven and welcomes contributions from users like you. Whether you've discovered a typo, want to clarify an explanation, or have a complete tutorial to share, your input helps make the platform better for everyone.

### Getting Started with Contributions

1. **Browse the documentation source** on [GitHub](https://github.com/opencadc/canfar)
2. **Set up local development**:

   ```bash
   git clone https://github.com/opencadc/canfar.git
   cd canfar
   pip install mkdocs mkdocs-material
   mkdocs serve
   ```

3. **View documentation**: Open `http://127.0.0.1:8000` in your browser

Changes to documentation files will automatically reload in your browser for real-time preview.

### Documentation Structure

Our documentation follows a clear structure designed for different user needs:

- **`get-started/`**: Quick setup for new users
- **`containers/`**: Container usage and building
- **`sessions/`**: Jupyter, desktop, and application sessions
- **`storage/`**: Data management and storage systems
- **`permissions`**: User management and access control
- **`concepts`**: Platform architecture and core concepts
- **`support/`**: Support resources, FAQ, and community information

### Writing Guidelines

**Markdown Style:**

- Use `#` for page titles, `##` for main sections, `###` for subsections
- Code blocks with language specification: ` ```python ` or ` ```bash `
- Inline code with single backticks: `variable_name` or `command --option`

**Admonitions for Important Information:**

```markdown
!!! note
    General information note

!!! tip "Pro Tip"
    Helpful advice for users

!!! warning
    Important cautions

!!! danger "Critical"
    Critical warnings

!!! example
    Code examples and demonstrations
```

**Writing for Different Audiences:**

**New Users:**

- Avoid jargon or explain technical terms clearly
- Provide step-by-step instructions
- Focus on common tasks and getting started
- Include plenty of examples

**Advanced Users:**

- Provide technical details and configuration options
- Include information on automation, APIs, and advanced workflows
- Assume familiarity with relevant technologies
- Link to detailed reference materials

### Contribution Process

1. **Make your changes** in the appropriate documentation files
2. **Test locally** using `mkdocs serve` to verify formatting
3. **Commit with clear messages**: `git commit -m "docs: Describe your change"`
4. **Submit a pull request** to the main repository
5. **Collaborate** with reviewers to refine your contribution

### Documentation Philosophy

We aim for documentation that is:

- **Accurate**: Technically correct and current
- **Clear**: Easy to understand without unnecessary jargon
- **Complete**: Covering essential aspects comprehensively
- **User-Friendly**: Well-structured and accessible

### Questions About Contributing?

- Open an issue on [GitHub](https://github.com/opencadc/canfar/issues)
- Ask on Discord in the community channels
- Email the CANFAR team at [support@canfar.net](mailto:support@canfar.net)

Your contributions help make CANFAR better for the entire astronomy community!

## 📞 Contact Information Summary

| Need | Contact | Response Time |
|------|---------|---------------|
| General support | [support@canfar.net](mailto:support@canfar.net) | 1-2 business days |
| Quick questions | [Discord Community](https://discord.gg/vcCQ8QBvBa) | Minutes to hours |

Remember: The CANFAR team is here to help you succeed in your research. Don't hesitate to reach out with questions, no matter how basic they might seem!
