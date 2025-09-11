# Contributed Applications

**Contributed Web-based Applications on CANFAR**

!!! abstract "🎯 What You'll Learn"
    - How to launch contributed applications on CANFAR
    - Where your data is stored and how to save results
    - How to contribute your own web application
    - Troubleshooting common issues

Contributed applications are specialised, community-developed web tools that expand CANFAR's capabilities. They integrate with CANFAR storage and authentication, are web-based for easy collaboration, and require no local installation. The catalogue of available applications evolves as the community contributes new tools.

!!! tip "Suggest New Applications"
    Have an idea for a new application? Jump on [discord](https://discord.gg/vcCQ8QBvBa), or contact [support@canfar.net](mailto:support@canfar.net) to discuss it.

## 🚀 Getting Started

1. Log into the [CANFAR Science Portal](https://www.canfar.net), click **+** to create a new session, and select `contributed`.
2. Choose an application from the dropdown menu.
3. Give your session a descriptive name and click "Launch."

Your application will start in 30-90 seconds.

!!! warning "Data Persistence"
    Contributed applications can access your files at `/arc/projects/[project]/` and `/arc/home/[user]/`. Always save important results to these paths, as other locations may not persist.

**Currently Available Applications:**

- **[marimo](https://marimo.io)** (`skaha/marimo:latest`): Reactive Python notebooks for reproducible analysis.
- **[VSCode on Browser](https://github.com/coder/code-server)** (`skaha/vscode:latest`): A browser-based development environment for collaborative projects (based on Visual Studio Code).

## 🧑‍💻 Contributing Your App

If you have a containerized web application, you can contribute it to the platform. The main requirements are that your application must expose a web interface on port 5000 and include a startup script at `/skaha/startup.sh`.

For detailed instructions, see the [Container Development](../containers/build.md) guide. We recommend contacting [support@canfar.net](mailto:support@canfar.net) to discuss your idea before you start.

## 🆘 Troubleshooting

- **Application doesn't load**: If your session doesn't start after 90 seconds, try a hard refresh of your browser page.
- **Data access issues**: These usually stem from incorrect file paths or permissions. Verify you are using the correct paths and have the necessary permissions.

## 🔗 What's Next?

To make the most of contributed applications, match the right tool to your workflow. Explore each application's capabilities and consider combining them with other CANFAR services like [Batch Processing](batch.md) for more powerful analysis. The [Storage Guide](../storage/index.md) will help you effectively manage your data.
