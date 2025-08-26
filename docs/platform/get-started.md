

# 🚀 Quick Setup

This guide walks you through getting started with CANFAR, from account setup to your first session. For details on accounts, storage, and containers, see the linked guides below.


## 1️⃣ Get Your CADC Account

If you are a first-time user, request a Canadian Astronomy Data Centre (CADC) account:

[🔗 Request CADC Account](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html){ .md-button .md-button--primary }

See [Accounts & Permissions](accounts.md) for more details.

!!! info "Account Processing Time"
    CADC accounts are typically approved within 1–2 business days.



## 2️⃣ Join or Create Your Research Group

Once you have a CADC account:

=== "Joining an Existing Group"
    Ask your collaboration administrator to add you via the [CADC Group Management Interface](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/).

=== "New Collaboration"
    Email [support@canfar.net](mailto:support@canfar.net) with:
    - Your project description
    - Expected team size
    - Storage requirements
    - Timeline

See [Accounts & Permissions](accounts.md) for group management details.


## 3️⃣ First Login and Setup

1. Login to [canfar.net](https://www.canfar.net) with your CADC credentials.
2. Accept Terms of Service to complete setup.
3. Access the [Image Registry](https://images.canfar.net) (required for private containers).

See [Container Usage](containers.md) for more about images and custom software.


## 4️⃣ Launch Your First Session

To start analyzing data, launch a Jupyter notebook:

1. Click **Science Portal** from the main menu.
2. Use the default settings.
3. Click **Launch**.
4. Wait about 30 seconds, then open your session.

🎉 You're ready to go! Your session includes Python, common astronomy packages, and access to shared storage.

See [Interactive Sessions](guides/interactive-sessions/index.md) for more session types and workflows.

!!! tip "Recommended Starting Point"
    Start with the default `astroml` container – it includes most common astronomy packages and is regularly updated.



## 📁 Understanding Your Workspace

See the [Storage Guide](guides/storage/index.md) for full details.

| Location | Purpose | Persistence | Best For |
|----------|---------|-------------|----------|
| `/arc/projects/[project]/` | Shared research data | ✅ Permanent, backed up | Datasets, results, shared code |
| `/arc/home/[user]/` | Personal files | ✅ Permanent, backed up | Personal configs, small files |
| `/scratch/` | Fast temporary space | ❌ Wiped at session end | Large computations, temporary files |



## 🤝 Collaboration Features

See [Accounts & Permissions](accounts.md) and [Storage Guide](guides/storage/index.md) for collaboration details.

### Session Sharing

Share running sessions with collaborators:

1. In your session, copy the session URL.
2. Share with team members (must be in the same group).
3. They can view and interact with your work in real time.

### Storage Sharing

All group members have access to `/arc/projects/[project]/` – perfect for:

- Sharing datasets and results
- Collaborative analysis scripts
- Common software environments
- Project documentation



## 🔗 What's Next?

Ready to dive deeper?

- **[📖 User Guide →](guides/index.md)** – Comprehensive documentation
- **[🗄️ Storage Guide →](guides/storage/index.md)** – Detailed storage management
- **[🐳 Container Guide →](containers.md)** – Using and building containers
- **[📡 Radio Astronomy →](guides/radio-astronomy/index.md)** – CASA, ALMA workflows



## 💬 Need Help?

- **[💬 Discord Community](https://discord.gg/vcCQ8QBvBa)** – Chat with other users
- **[❓ FAQ](../faq.md)** – Common questions and solutions

---


