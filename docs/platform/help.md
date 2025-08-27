# Getting Help and Support

The CANFAR Science Platform provides multiple channels for getting help, from self-service documentation to direct support. This section guides you to the right resources for your needs.


!!! info "Quick Links"
    - [Get Started Guide](get-started.md)
    - [FAQ](../faq.md)
    - [Platform Concepts](concepts.md)
    - [Containers](containers.md)
    - [Interactive Sessions](guides/interactive-sessions/index.md)
    - [Batch Jobs](batch-jobs.md)
    - [Radio Astronomy Guide](guides/radio-astronomy/index.md)
    - [Contact Support](#contact-support)


### New to CANFAR?

- **[Get Started Guide](get-started.md)**: 10-minute quick start
- **[First Login](accounts.md)**: Account setup and access
- **[Choose Your Interface](guides/interactive-sessions/index.md)**: Pick the right session type

### Having Problems?

- **[FAQ](../faq.md)**: Common questions and solutions
- **[Troubleshooting](#troubleshooting)**: Diagnostic steps for common issues
- **[Contact Support](#contact-support)**: Direct help from CANFAR staff

### Want to Learn More?

- **[User Guide](guides/index.md)**: Comprehensive platform documentation
- **[Radio Astronomy Guide](guides/radio-astronomy/index.md)**: Specialized astronomy workflows
- **[Community](#community-support)**: Connect with other users

## Self-Help Resources

### Documentation

**User Guide Sections**:

- **[Concepts](concepts.md)**: Understanding the platform architecture
- **[Storage](guides/storage/index.md)**: Managing your data effectively
- **[Containers](containers.md)**: Using and building software environments
- **[Interactive Sessions](guides/interactive-sessions/index.md)**: Jupyter, Desktop, CARTA
- **[Batch Jobs](batch-jobs.md)**: Automated and large-scale processing
- **[Radio Astronomy](guides/radio-astronomy/index.md)**: CASA and radio-specific workflows

**Tutorials**:

- **[Data Analysis Examples](guides/interactive-sessions/index.md)**: Common astronomy workflows
- **[Radio Astronomy Guide](guides/radio-astronomy/index.md)**: CASA and interferometry
- **[Container Building](containers.md)**: Create custom environments

### Video Resources

**Getting Started Videos** (coming soon):

- Platform overview and navigation
- Creating your first session
- Data management basics
- Collaboration features

**Workflow Demonstrations**:

- Optical photometry pipeline
- Radio interferometry reduction
- Multi-wavelength analysis

## Troubleshooting

### Quick Diagnostic Steps

When you encounter issues, try these steps first:

1. **Check System status**: Look for maintenance announcements
2. **Try a different browser**: Chrome and Firefox work best
3. **Clear browser cache**: Remove cookies and cached data
4. **Try incognito mode**: Eliminates browser extension conflicts
5. **Check your network**: Ensure stable internet connection

### Common Issues and Solutions

#### Session Won't Start

**Symptoms**: Session creation fails or hangs

**Solutions**:
- Reduce resource requirements (memory/CPU)
- Try during off-peak hours (evenings, weekends)
- Select a different container image
- Check group permissions

#### Can't Access Files

**Symptoms**: Files missing or permission denied

**Solutions**:
```bash
# Check file locations
ls /arc/home/[user]/     # Personal storage
ls /arc/projects/           # Group storage

# Check permissions
ls -la /arc/projects/[project]/
getfacl /arc/projects/[project]/
```

- Verify you're in the correct group
- Check file paths are correct
- Contact group administrator


#### Performance Issues

!!! tip "Advanced: Optimizing Performance"
    - Use [Batch Jobs](batch-jobs.md) for large-scale or automated processing.
    - Monitor session resource usage with `canfar stats` and [session info](concepts.md#sessions).
    - Store temporary files in `/scratch/` for faster I/O.
    - For parallel workloads, see [Distributed Computing](../client/helpers.md).

**Symptoms**: Slow processing or unresponsive interface

**Solutions**:
- Monitor resource usage with `htop`
- Close unnecessary applications
- Use scratch storage (`/scratch/`) for temporary files
- Consider requesting more resources


#### Browser Compatibility

!!! tip "Advanced: Browser Automation"
    - Use browser profiles/extensions for session isolation.
    - Automate repetitive browser tasks with [Selenium](https://www.selenium.dev/) or [Playwright](https://playwright.dev/).

**Symptoms**: Interface doesn't load or behaves incorrectly

**Solutions**:
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


---

!!! info "See Also"
    - [Bug Reports](../bug-reports.md)
    - [Security](../security.md)
    - [Contributing](#contributing-to-documentation)

### When to Contact Support

Contact [support@canfar.net](mailto:support@canfar.net) for:

- **Account issues**: Access problems, group membership
- **Technical problems**: Persistent errors, system failures
- **Data recovery**: Lost or corrupted files
- **Resource requests**: Increased storage or compute allocations
- **Software installation**: Help with complex software setups

### How to Write Effective Support Requests

Include these details in your support email:

**Essential information**:

Example:
```
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

**Additional helpful information**:

- Screenshots of error messages
- Session IDs for failed jobs
- File paths for missing data
- Group names for permission issues

### Expetected Response Times

- **Standard support**: 1-2 business days
- **Urgent issues**: Same day during business hours
- **Emergency outages**: Immediate response during business hours

**Business hours**: Monday-Friday, 9 AM - 5 PM Pacific Time


### Support Escalation

For urgent research deadlines or critical system issues:

1. **Mark email as urgent**: Use "URGENT" in subject line
2. **Explain deadline**: Include your research timeline
3. **Provide context**: Explain impact of the issue
4. **Follow up**: Call if no response within expected timeframe


## Community Support


### Discord Community

!!! tip "Advanced: Community Collaboration"
    - Share workflow examples in Discord for peer review.
    - Use Discord threads for project-specific discussions.
    - Join [Office Hours](#office-hours) for live troubleshooting.

Join our Discord server for peer support and community interaction:

- **Quick questions**: Get fast answers from other users
- **Tips and tricks**: Share and learn best practices
- **Collaboration**: Find research partners and collaborators
- **Announcements**: Stay updated on new features and maintenance

**Discord invite**: [Join CANFAR Discord](https://discord.gg/vcCQ8QBvBa)

**Community guidelines**:

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



### Office Hours

!!! info "Office Hours: Get Real-Time Help"
    - Thursdays 2-3 PM Pacific Time
    - [Join via Discord](https://discord.gg/vcCQ8QBvBa)
    - Bring your code, workflows, or error messages for live support.

**Virtual office hours**: Thursdays 2-3 PM Pacific Time

- **Format**: Video conference with screen sharing
- **Topics**: Any CANFAR-related questions
- **Registration**: Not required, drop-in welcome
- **Recording**: Sessions recorded for later viewing

**What to bring**:
- Specific questions or problems
- Example code or workflows
- Error messages or screenshots


### Peer Mentoring

!!! tip "Advanced: Become a Mentor"
    - Experienced users can volunteer as mentors via [support@canfar.net](mailto:support@canfar.net).
    - Mentors help with onboarding, troubleshooting, and advanced workflows.

**Experienced user program**: Connect new users with experienced mentors

- **Mentors**: Volunteer researchers who use CANFAR regularly
- **Support areas**: Platform basics, specific software, research workflows
- **Matching**: Based on research area and experience level
- **Contact**: Email support to request mentor connection


### Community Contributions

!!! tip "Advanced: Share Your Expertise"
    - Submit tutorials or workflow examples to the documentation via GitHub.
    - Answer questions in Discord and GitHub Issues.
    - Report bugs and suggest features to improve the platform for all users.

**Ways to help other users**:

- **Answer questions**: Respond to Discord and community discussions
- **Share tutorials**: Create workflow examples
- **Report bugs**: Help improve platform stability
- **Suggest features**: Propose improvements

---

## Contributing to Documentation

The CANFAR Science Platform documentation is community-driven, and we welcome contributions from users who want to help improve the platform for everyone.

### 📝 How to Contribute

**Quick Edits**:
- Use the "Edit this page" link (pencil icon) on any documentation page
- Makes suggestions directly on GitHub
- Perfect for typos, clarifications, and small updates

**Larger Contributions**:
- Set up local development environment
- Create comprehensive new sections
- Major restructuring or new guides

### 🚀 Local Development Setup

**Prerequisites**:
- Python 3.x and pip
- Git for version control

**Setup Steps**:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/opencadc/canfar.git
   cd science-containers
   ```

2. **Install dependencies**:
NB: at the time of writing `poetry` was a good tool to deal with python dependencies. Now `uv` or `pixi` may be better choices.
   ```bash
   # You may want to install `poetry` if you don't have it
   # See: https://python-poetry.org/docs/#installation
   
   poetry install
   ```

3. **Start development server**:
   ```bash
   poetry shell
   mkdocs serve
   ```

4. **View documentation**: Open `http://127.0.0.1:8000` in your browser

Changes to documentation files will automatically reload in your browser for real-time preview.


### 📁 Documentation Structure

!!! info "Explore More Documentation"
    - [Get Started](get-started.md)
    - [FAQ](../faq.md)
    - [Platform Concepts](concepts.md)
    - [Containers](containers.md)
    - [Interactive Sessions](guides/interactive-sessions/index.md)
    - [Batch Jobs](batch-jobs.md)
    - [Radio Astronomy](guides/radio-astronomy/index.md)

Our documentation follows a clear structure designed for different user needs:

- **`get-started/`**: Quick setup for new users
- **`user-guide/`**: Comprehensive platform documentation
  - `concepts/`: Platform architecture and core concepts
  - `accounts-permissions/`: User management and access control  
  - `storage/`: Data management and storage systems
  - `containers/`: Container usage and building
  - `interactive-sessions/`: Jupyter, desktop, and application sessions
  - `batch-jobs/`: Automated and large-scale processing
  - `radio-astronomy/`: CASA and radio-specific workflows
- **`faq/`**: Frequently asked questions and troubleshooting
- **`help/`**: Support resources and community information

### ✍️ Writing Guidelines

**Markdown Style**:
- Use `#` for page titles, `##` for main sections, `###` for subsections
- Code blocks with language specification: ` ```python ` or ` ```bash `
- Inline code with single backticks: `variable_name` or `command --option`

**Admonitions for Important Information**:
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

**Writing for Different Audiences**:

**New Users**:
- Avoid jargon or explain technical terms clearly
- Provide step-by-step instructions
- Focus on common tasks and getting started
- Include plenty of examples


**Advanced Users**:
- Provide technical details and configuration options
- Use [CANFAR CLI](../cli/cli-help.md) for automation and scripting
- Explore [Distributed Computing](../client/helpers.md) for parallel workloads
- Integrate CANFAR with external tools (e.g., Jupyter, Docker, GitHub Actions)
- Link to detailed reference materials and example scripts

### 🔄 Contribution Process

1. **Make your changes** in the appropriate documentation files
2. **Test locally** using `mkdocs serve` to verify formatting
3. **Commit with clear messages**: `git commit -m "docs: Describe your change"`
4. **Submit a pull request** to the main repository
5. **Collaborate** with reviewers to refine your contribution

### 📚 Documentation Philosophy

We aim for documentation that is:
- **Accurate**: Technically correct and current
- **Clear**: Easy to understand without unnecessary jargon
- **Complete**: Covering essential aspects comprehensively
- **User-Friendly**: Well-structured and accessible

### ❓ Questions About Contributing?

- Open an issue on [GitHub](https://github.com/opencadc/canfar/issues)
- Ask on Discord in the community channels
- Email the CANFAR team at [support@canfar.net](mailto:support@canfar.net)

Your contributions help make CANFAR better for the entire astronomy community!

---

## Additional Resources

### External Documentation

**Related platforms**:
- **CADC Archive**: [cadc-ccda.hia-iha.nrc-cnrc.gc.ca](https://cadc-ccda.hia-iha.nrc-cnrc.gc.ca)
- **VOSpace**: [vospace.canfar.net](https://www.canfar.net)
- **Science Portal**: [science.canfar.net](https://www.canfar.net)

**Software documentation**:
- **CASA**: [casa.nrao.edu](https://casa.nrao.edu)
- **AstroPy**: [astropy.org](https://astropy.org)
- **Jupyter**: [jupyter.org](https://jupyter.org)
- **Docker**: [docs.docker.com](https://docs.docker.com)

### Research Collaboration

**Finding collaborators**:
- Discord community channels
- Conference networking
- Shared project spaces
- Research group connections

**Collaboration tools**:
- Real-time session sharing
- Shared storage spaces
- Version control with Git
- Communication through Discord

### Staying Updated

**Announcements**:
- Email notifications for maintenance
- Discord #announcements channel
- Science Portal news section

## Emergency Contacts

### System Outages

**Planned maintenance**: Announced 48+ hours in advance via email and Discord

**Unplanned outages**: 
- Check status.canfar.net for current status (when available)
- Email [support@canfar.net](mailto:support@canfar.net) if status unclear

### Critical Data Issues

**Data loss or corruption**:
1. **Stop all activity**: Prevent further damage
2. **Document the issue**: Note exactly what happened
3. **Contact support immediately**: Mark email as URGENT
4. **Preserve evidence**: Don't delete or modify files

**Backup and recovery**:
- Daily snapshots of `/arc/` storage
- 30-day retention period
- Point-in-time recovery available
- Contact support for restoration requests

### Security Incidents

**Suspected security breach**:
1. **Change credentials**: Update certificates immediately
2. **Report incident**: Email [support@canfar.net](mailto:support@canfar.net)
3. **Document details**: What you observed and when
4. **Follow instructions**: Wait for security team guidance

**Prevention**:
- Never share your certificates
- Keep software updated
- Report suspicious activity

---

## Contributing to Documentation

The CANFAR Science Platform documentation is community-driven, and we welcome contributions from users who want to help improve the platform for everyone.

### 📝 How to Contribute

**Quick Edits**:

- Use the "Edit this page" link (pencil icon) on any documentation page
- Makes suggestions directly on GitHub
- Perfect for typos, clarifications, and small updates

**Larger Contributions**:

- Set up local development environment
- Create comprehensive new sections
- Major restructuring or new guides

### 🚀 Local Development Setup

**Prerequisites**:

- Python 3.x and pip
- Git for version control

**Setup Steps**:

1. **Clone the repository**:

   ```bash
   git clone https://github.com/opencadc/canfar.git
   cd science-containers
   ```

2. **Install dependencies** (using Poetry):

   ```bash
   # Install Poetry if you don't have it
   # See: https://python-poetry.org/docs/#installation
   
   poetry install
   ```

3. **Start development server**:

   ```bash
   poetry shell
   mkdocs serve
   ```

4. **View documentation**: Open `http://127.0.0.1:8000` in your browser

Changes to documentation files will automatically reload in your browser for real-time preview.

### 📁 Documentation Structure

Our documentation follows a clear structure designed for different user needs:

- **`get-started/`**: Quick setup for new users
- **`guides/`**: Comprehensive platform documentation
  - `containers/`: Container usage and building
  - `interactive-sessions/`: Jupyter, desktop, and application sessions
  - `radio-astronomy/`: CASA and radio-specific workflows
  - `storage/`: Data management and storage systems
- **`accounts/`**: User management and access control
- **`batch-jobs/`**: Automated and large-scale processing
- **`concepts/`**: Platform architecture and core concepts
- **`faq/`**: Frequently asked questions and troubleshooting
- **`help/`**: Support resources and community information

### ✍️ Writing Guidelines

**Markdown Style**:

- Use `#` for page titles, `##` for main sections, `###` for subsections
- Code blocks with language specification: ` ```python ` or ` ```bash `
- Inline code with single backticks: `variable_name` or `command --option`

**Admonitions for Important Information**:

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

**Writing for Different Audiences**:

**New Users**:

- Avoid jargon or explain technical terms clearly
- Provide step-by-step instructions
- Focus on common tasks and getting started
- Include plenty of examples

**Advanced Users**:

- Provide technical details and configuration options
- Include information on automation, APIs, and advanced workflows
- Assume familiarity with relevant technologies
- Link to detailed reference materials

### 🔄 Contribution Process

1. **Make your changes** in the appropriate documentation files
2. **Test locally** using `mkdocs serve` to verify formatting
3. **Commit with clear messages**: `git commit -m "docs: Describe your change"`
4. **Submit a pull request** to the main repository
5. **Collaborate** with reviewers to refine your contribution

### 📚 Documentation Philosophy

We aim for documentation that is:

- **Accurate**: Technically correct and current
- **Clear**: Easy to understand without unnecessary jargon
- **Complete**: Covering essential aspects comprehensively
- **User-Friendly**: Well-structured and accessible

### ❓ Questions About Contributing?

- Open an issue on [GitHub](https://github.com/opencadc/science-containers/issues)
- Ask on Discord in the community channels
- Email the CANFAR team at [support@canfar.net](mailto:support@canfar.net)

Your contributions help make CANFAR better for the entire astronomy community!

---

## Contact Information Summary

| Need | Contact | Response Time |
|------|---------|---------------|
| General support | [support@canfar.net](mailto:support@canfar.net) | 1-2 business days |
| Quick questions | [Discord Community](https://discord.gg/vcCQ8QBvBa) | Minutes to hours |
| Security issues | [security@canfar.net](mailto:security@canfar.net) | Same day |
| Documentation | [support@canfar.net](mailto:support@canfar.net) | 1-2 business days |
| Office hours | Video conference | Thursdays 2-3 PM PT |

Remember: The CANFAR team is here to help you succeed in your research. Don't hesitate to reach out with questions, no matter how basic they might seem!
