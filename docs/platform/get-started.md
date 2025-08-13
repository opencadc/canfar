# 🚀 Quick Setup

This guide will walk you through the complete process of getting started with CANFAR, from account setup to your first analysis session.

## Step 1: Get Your CADC Account

**First time user?** You need a Canadian Astronomy Data Centre (CADC) account:

[**🔗 Request CADC Account**](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html){ .md-button .md-button--primary }

!!! info "Account Processing Time"
    CADC accounts are typically approved within 1-2 business days.

## Step 2: Join or Create Your Research Group

**Once you have a CADC account:**

=== "Joining Existing Group"
    Ask your collaboration administrator to add you via the [CADC Group Management Interface](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/)

=== "New Collaboration"
    Email [support@canfar.net](mailto:support@canfar.net) with:
    
    - Your research project description
    - Expected team size
    - Storage requirements
    - Timeline

## Step 3: First Login and Setup

1. **Login to CANFAR** - Visit [canfar.net](https://www.canfar.net) with your CADC credentials
2. **Accept Terms of Service** - Complete the initial setup
3. **Access Image Registry** - Login to [images.canfar.net](https://images.canfar.net) (required for private containers)

!!! tip "Pro Tip"
    Ask your group administrator to grant you read access to private container images if your collaboration uses custom software.

## Step 4: Launch Your First Session

Try launching a Jupyter notebook to start analyzing data:

1. Click **_Science Portal_** from the main menu
2. Use the **_default_** settings as is
3. Click **_Launch_**
4. Wait **_~30s_** and click to open your session

🎉 **You're ready to go!** Your session includes Python, common astronomy packages, and access to shared storage.

!!! tip "Recommended Starting Point"
    Start with the default `astroml` container - it includes most common astronomy packages and is regularly updated with the latest software.

# 📁 Understanding Your Workspace

Now that you're logged in, here's how CANFAR organizes your data:

| Location | Purpose | Persistence | Best For |
|----------|---------|-------------|----------|
| `/arc/projects/yourgroup/` | Shared research data | ✅ Permanent, backed up | Datasets, results, shared code |
| `/arc/home/yourusername/` | Personal files | ✅ Permanent, backed up | Personal configs, small files |
| `/scratch/` | Fast temporary space | ❌ Wiped at session end | Large computations, temporary files |

# 🤝 Collaboration Features

## Session Sharing
Share running sessions with collaborators:

1. In your session, copy the session URL
2. Share with team members (must be in same group)
3. They can view and interact with your work in real-time

## Storage Sharing
All group members have access to `/arc/projects/yourgroup/` - perfect for:

- Sharing datasets and results
- Collaborative analysis scripts
- Common software environments
- Project documentation

# 🔗 What's Next?

Ready to dive deeper? 

- **[User Guide →](guides/index.md)** - Comprehensive documentation
- **[Storage Guide →](guides/storage/index.md)** - Detailed storage management
- **[Container Guide →](containers.md)** - Using and building containers
- **[Radio Astronomy →](guides/radio-astronomy/index.md)** - CASA, ALMA workflows

# 💬 Need Help?

- **[💬 Discord Community](https://discord.gg/vcCQ8QBvBa)** - Chat with other users
- **[❓ FAQ](../faq.md)** - Common questions and solutions

---


