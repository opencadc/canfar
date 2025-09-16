# 🚀 Getting Started with CANFAR

**Guide to setting up and using the CANFAR Science Platform for astronomical research.**


    **Essential Resources:**
    - [Permissions Guide](permissions.md): Account set-up and group management
    - [Sessions Overview](sessions/index.md): Interactive computing environments
    - [Storage Guide](storage/index.md): Data management and file systems
    - [Container Guide](containers/index.md): Software environments and registries
    - [Support Centre](support/index.md): Help resources and FAQ


## 1️⃣ Get Your CADC Account

If you are a first-time user, request a Canadian Astronomy Data Centre (CADC) account:

[🔗 Request CADC Account](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html){ .md-button .md-button--primary }

See [Accounts & Permissions](permissions.md) for more details.


!!! info "Account Processing Time"
    CADC accounts are typically approved within 1–2 business days.
    For troubleshooting account issues, see [FAQ](support/faq.md) or [Contact Support](support/index.md).



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


See [Permissions Guide](permissions.md) for group management details. For advanced collaboration, see [Storage Guide](storage/index.md).


## 3️⃣ First Login and Set-up

1. Login to [canfar.net](https://www.canfar.net) with your CADC credentials.
2. Accept Terms of Service to complete set-up.
3. Optional (for private containers): Access the [Image Registry](https://images.canfar.net)

See [Container Guide](containers/index.md) for more about images and custom software. For building your own containers, see [Building Containers](containers/build.md).


## 4️⃣ Launch Your First Session

To start analyzing data, launch a Jupyter notebook:

1. Click **Science Portal** from the main menu.
2. Use the default settings.
3. Click **Launch**.
4. Wait about 30 seconds, then open your session.

🎉 You're ready to go! Your session includes Python, common astronomy packages, and access to shared storage.


See [Sessions Overview](sessions/index.md) for more session types and workflows. For automation, see [CANFAR Python Client](../client/home.md).


!!! tip "Recommended Starting Point"
    Start with the default `astroml` container – it includes most common astronomy packages and is regularly updated.

!!! tip "Advanced: Custom Containers"
    - Build your own containers for specialised workflows. See [Building Containers](containers/build.md).
    - Use [Harbor Registry](https://images.canfar.net/) to browse and manage images.



## 📁 Understanding Your Workspace


See the [Storage Guide](storage/index.md) for full details. For VOSpace scripting, see [VOSpace API](storage/vospace.md).

| Location | Purpose | Persistence | Best For |
|----------|---------|-------------|----------|
| `/arc/projects/[project]/` | Shared research data | ✅ Permanent, backed up | Datasets, results, shared code |
| `/arc/home/[user]/` | Personal files | ✅ Permanent, backed up | Personal configs, small files |
| `/scratch/` | Fast temporary space | ❌ Wiped at session end | Large computations, temporary files |



## 🤝 Collaboration Features


See [Permissions Guide](permissions.md) and [Storage Guide](storage/index.md) for collaboration details. For team onboarding, see [Getting Started](get-started.md).

### Storage Sharing

All group members have access to `/arc/projects/[project]/` – perfect for:

- Sharing datasets and results
- Collaborative analysis scripts
- Common software environments
- Project documentation


## 💬 Need Help?

- **[💬 Discord Community](https://discord.gg/vcCQ8QBvBa)** – Chat with other users
- **[🆘 Support Centre](support/index.md)** – Help resources and contact information

---


