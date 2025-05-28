# Frequently Asked Questions

Common questions and solutions for using the CANFAR Science Platform.

## 🚀 Getting Started

### How do I get access to CANFAR?
1. **Request a CADC account**: [Account request form](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html)
2. **Get portal authorization**: Either join an existing collaboration or request new project access
3. **Login**: Visit [CANFAR Portal](https://www.canfar.net) with your CADC credentials

[**→ Detailed access guide**](../getting-started/access.md)

### What's the difference between CADC and CANFAR accounts?
- **CADC account**: Your basic astronomy data center account (required for everything)
- **CANFAR portal access**: Additional authorization to use the science platform (requested separately)

### How long does account approval take?
- **CADC account**: 1-2 business days
- **Portal authorization**: 1-3 business days for existing collaborations, 1-2 weeks for new projects

---

## 🖥️ Sessions and Computing

### My session is stuck in "Pending" state
This usually means the platform can't launch your container. Try these steps:

1. **Reset CLI Secret**:
   - Login to [images.canfar.net](https://images.canfar.net)
   - Go to User Profile → CLI Secret → Reset
   - Delete the pending session and try again

2. **Check permissions**: Verify you have access to the container image
3. **Resource availability**: Platform may be waiting for available resources
4. **Contact support**: If issue persists, email [support@canfar.net](mailto:support@canfar.net)

### How many sessions can I run simultaneously?
**Maximum 3 sessions** at once, regardless of type (notebook, desktop, CARTA).

### How long do sessions last?
- **Default duration**: 4 days
- **Renewal**: Click the ⏰ clock icon on any session to extend
- **Automatic termination**: Sessions end after 4 days if not renewed

### Can I run sessions in the background?
Sessions continue running even if you close your browser. You can reconnect anytime during the 4-day period.

---

## 💾 Storage and Files

### Where should I put my files?
```
/arc/home/username     ← Personal configs and private files
/arc/projects/group    ← Shared research data and results
```

**Use `/arc/projects` for almost everything** - it's optimized for collaboration and large datasets.

### How much storage do I have?
Storage quotas vary by project, typically 100GB to 10TB. Check usage with:
```bash
df -h /arc/projects/your-group
```

### How do I transfer large datasets?
- **Small files** (<100MB): Upload via browser or notebook interface
- **Large files**: Use [sshfs](../general/General_tools/sshfs-setup.md) or [vostools](../general/General_tools/vospace-tools.md)
- **Archives**: Download directly to `/arc/projects` from within sessions

[**→ Complete data transfer guide**](../data-transfer-guide.md)

### My files disappeared!
Files in `/arc` are persistent and backed up. If you can't find files:
1. **Check the path**: Ensure you're looking in `/arc/projects/your-group`
2. **Check permissions**: You might not have read access to certain directories
3. **Different session**: Files are shared across all sessions
4. **Contact support**: We maintain 30-day backups of deleted files

---

## 🔧 Technical Issues

### The interface is slow or unresponsive
1. **Check internet connection**: CANFAR requires good bandwidth for remote desktop
2. **Try different browser**: Chrome/Firefox work best
3. **Reduce resource usage**: Close unnecessary applications in your session
4. **Restart session**: Sometimes a fresh session resolves performance issues

### I can't install software packages
**In notebooks**:
```bash
# Install Python packages
pip install --user package-name

# Install conda packages  
conda install -c conda-forge package-name
```

**In desktop**: Use system package managers (apt, yum) - you have sudo access

**For persistent installs**: Consider building a [custom container](../advanced/containers.md)

### Graphics/GUI applications don't work
- **Check DISPLAY variable**: Should be set automatically
- **Try restarting the session**
- **Browser compatibility**: Some browsers handle VNC better than others
- **Disable browser extensions**: Ad blockers can interfere with VNC

### How do I test containers on my Mac?
```bash
# Enable X11 forwarding
xhost + 127.0.0.1

# Run with display forwarding
docker run -e DISPLAY=host.docker.internal:0 your-container
```

---

## 👥 Collaboration and Permissions

### How do I share files with collaborators?
1. **Put files in project space**: `/arc/projects/your-group/`
2. **Set permissions**: Use [group management](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/)
3. **Organize clearly**: Use descriptive directory names and README files

### How do I add someone to my project?
Only project administrators can add members:
1. Go to [CADC Groups](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/)
2. Find your project group
3. Add the person's CADC username

### Can I make my files public?
Yes, but be careful with sensitive data. Use the [storage interface](https://www.canfar.net/storage/arc/list) to set file permissions.

---

## 🐳 Containers and Software

### What software is available?
- **Notebooks**: Python, R, Julia with astronomy libraries
- **Desktop**: CASA, DS9, TOPCAT, standard Linux tools
- **CARTA**: Radio astronomy image viewer
- **Custom**: Build your own containers for specialized software

[**→ Complete software list**](../complete/available-containers.md)

### Can I use my own software?
Yes! You can:
1. **Install in session**: Use pip, conda, or package managers
2. **Build custom container**: For persistent, shareable environments
3. **Request software**: Ask support to add popular packages

### How do I request new software?
Email [support@canfar.net](mailto:support@canfar.net) with:
- Software name and version
- Installation instructions
- Justification for community use

---

## 🔄 Data and Workflows

### Can I access external databases?
Yes, most astronomical databases are accessible:
- **MAST, IRSA, ESO**: Direct API access
- **Vizier, SIMBAD**: Via astroquery
- **Custom APIs**: HTTP/HTTPS connections work normally

### How do I cite CANFAR in publications?
```
The authors acknowledge the use of the Canadian Advanced Network for 
Astronomy Research (CANFAR) Science Platform. Our work used the facilities 
of the Canadian Astronomy Data Center, operated by the National Research 
Council of Canada with the support of the Canadian Space Agency, and CANFAR, 
a consortium that serves the data-intensive storage, access, and processing 
needs of university groups and centers engaged in astronomy research 
(Gaudet et al. 2010).
```

### Can I run jobs without a GUI (headless)?
Yes, but with limitations. Contact [support@canfar.net](mailto:support@canfar.net) before using batch processing.

[**→ Headless Execution Guide**](../headless-execution-guide.md)

---

## 🚨 Emergency Procedures

### I accidentally deleted important files
1. **Stop immediately**: Don't create new files in the same location
2. **Contact support**: Email [support@canfar.net](mailto:support@canfar.net) with:
   - File paths that were deleted
   - Approximate deletion time
   - File importance level
3. **Backup policy**: We maintain 30-day backups

### My session crashed and I lost work
- **Notebooks**: Jupyter auto-saves every 2 minutes
- **Desktop applications**: Save work frequently to `/arc/projects`
- **Recovery**: Restart the session and check auto-saved files

### Platform seems down
1. **Check status**: Monitor [CANFAR Twitter](https://twitter.com/CANFAR_CADC) for updates
2. **Try different interface**: If notebooks fail, try desktop
3. **Community**: Ask in [Slack channel](https://cadc.slack.com/archives/C01K60U5Q87)
4. **Report**: Email [support@canfar.net](mailto:support@canfar.net) with details

---

## 📞 Getting More Help

### Quick Support
- **💬 Slack**: [CANFAR Channel](https://cadc.slack.com/archives/C01K60U5Q87) - fastest for urgent issues
- **📧 Email**: [support@canfar.net](mailto:support@canfar.net) - for detailed problems
- **🐛 Bug reports**: [GitHub Issues](https://github.com/opencadc/science-platform/issues)

### What to Include in Support Requests
1. **Your CADC username**
2. **What you were trying to do**
3. **What happened instead**
4. **Error messages** (copy/paste or screenshots)
5. **Browser and OS** you're using
6. **Time when the issue occurred**

### Response Times
- **Slack**: Usually within a few hours during business days
- **Email**: 1-2 business days for most issues
- **Emergency**: Call CADC directly for critical data loss

The CANFAR team is committed to helping you succeed with your research!
