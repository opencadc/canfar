# Getting Started with CANFAR

**Quick start guide to get you up and running with CANFAR Science Platform in minutes**

CANFAR provides cloud-based astronomy computing with interactive sessions, shared storage, and pre-built software containers. Perfect for grad students, astronomers, and project managers who need powerful computing resources for data analysis.

## 🚀 Quick Setup (10 minutes)

### Step 1: Get Access

**First time user?** You need a Canadian Astronomy Data Centre (CADC) account:

[**🔗 Request CADC Account**](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html){ .md-button .md-button--primary }

!!! info "Account Processing Time"
    CADC accounts are typically approved within 1-2 business days.

**Once you have a CADC account:**

=== "Joining Existing Group"
    Ask your collaboration administrator to add you via the [CADC Group Management Interface](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/)

=== "New Collaboration"
    Email [support@canfar.net](mailto:support@canfar.net) with:
    
    - Your research project description
    - Expected team size
    - Storage requirements
    - Timeline

### Step 2: First Login

1. **Access the portal:** [https://www.canfar.net](https://www.canfar.net)
2. **Login** with your CADC credentials
3. **Accept** the platform terms of service

### Step 3: Launch Your First Session

Try launching a Jupyter notebook to start analyzing data:

1. Click **"Science Portal"** from the main menu
2. Select **"notebook"** from the session types
3. Choose **"astroml"** container (default astronomy environment)
4. Click **"Launch"**
5. Wait ~30 seconds for your session to start

🎉 **You're ready to go!** Your session includes Python, common astronomy packages, and access to shared storage.

## 📁 Understanding Storage

CANFAR provides different storage areas for different needs:

| Location | Purpose | Persistence | Best For |
|----------|---------|-------------|----------|
| `/arc/projects/yourgroup/` | Shared research data | ✅ Permanent, backed up | Datasets, results, shared code |
| `/arc/home/yourusername/` | Personal files | ✅ Permanent, backed up | Personal configs, small files |
| `/scratch/` | Fast temporary space | ❌ Wiped at session end | Large computations, temporary files |

## 🤝 Collaboration Features

### Session Sharing
Share running sessions with collaborators:

1. In your session, copy the session URL
2. Share with team members (must be in same group)
3. They can view and interact with your work in real-time

### Storage Sharing
All group members have access to `/arc/projects/yourgroup/` - perfect for:

- Sharing datasets and results
- Collaborative analysis scripts
- Common software environments
- Project documentation

## 🔗 What's Next?

Ready to dive deeper? 

- **[User Guide →](../user-guide/index.md)** - Comprehensive documentation
- **[Storage Guide →](../user-guide/storage/index.md)** - Detailed storage management
- **[Container Guide →](../user-guide/containers/index.md)** - Using and building containers
- **[Radio Astronomy →](../user-guide/radio-astronomy/index.md)** - CASA, ALMA workflows

## 💬 Need Help?

- **[💬 Discord Community](https://discord.gg/YOUR_INVITE_LINK)** - Chat with other users
- **[📧 Email Support](mailto:support@canfar.net)** - Direct technical support
- **[❓ FAQ](../faq/index.md)** - Common questions and solutions

---

!!! tip "Pro Tip"
    Start with the default `astroml` container - it includes most common astronomy packages and is regularly updated with the latest software.
