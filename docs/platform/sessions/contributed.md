# Contributed Applications

## Community-developed tools and specialised research applications

!!! abstract "🎯 What You'll Learn"
    - What contributed applications are and when to use them
    - How to launch and size contributed application sessions
    - How these apps integrate with CANFAR storage and authentication
    - Best practices for collaboration, performance, and security

## 📋 Overview

Contributed applications expand CANFAR's capabilities beyond standard notebook and desktop environments. These specialised tools are developed by the CANFAR community and external collaborators to address specific astronomical workflows and research needs not well-served by conventional interfaces.

### What Are Contributed Applications?

Contributed applications are purpose-built web tools that seamlessly integrate with CANFAR's infrastructure while offering unique capabilities:

- **Specialised interfaces**: Tools designed for specific research tasks
- **Community-driven**: Developed by CANFAR users for CANFAR users  
- **Seamless integration**: Full access to CANFAR storage and authentication
- **Web-based access**: No local software installation required
- **Collaborative ready**: Easy sharing and real-time collaboration

### Benefits and Use Cases

**Extending CANFAR's Capabilities:**

- **Modern development environments**: Browser-based IDEs and reactive notebooks
- **Specialised analysis tools**: Applications tailored for specific astronomical workflows  
- **Enhanced collaboration**: Real-time sharing and team development
- **No installation hassles**: Access powerful tools without local setup
- **Community innovation**: Cutting-edge tools shared across the research community

**Common Applications:**

- **Interactive development**: Modern Python environments and browser IDEs
- **Reactive computing**: Notebooks that update automatically as you modify code
- **Collaborative coding**: Shared development environments for team projects
- **Specialised workflows**: Tools designed for specific research methodologies

### Available Applications

The catalogue evolves regularly as community members contribute new tools:

**Currently Available:**

| Application | Container | Best For |
|-------------|-----------|----------|
| **Marimo** | `images.canfar.net/cadc/marimo:latest` | Reactive Python notebooks, stored as pure Python files |
| **VSCode Browser** | `images.canfar.net/cadc/vscode:latest` | Full IDE experience for software development |

**Coming Soon:**

The ecosystem continues to expand with reactive notebooks, browser IDEs, and specialised computational interfaces contributed by the community. Applications in development focus on time-series analysis, interactive visualisation, and collaborative annotation tools.

!!! tip "Suggest New Applications"
    Have an idea for a contributed application? Contact [support@canfar.net](mailto:support@canfar.net) to discuss community needs and development possibilities.

## 🚀 Getting Started

### Accessing the Application Catalogue

To start with contributed applications, log into the [CANFAR Science Portal](https://www.canfar.net), click the plus sign (**+**) to create a new session, and select `contributed` as your session type to open the specialised application catalogue.

![Select Contributed Session](images/contributed/1_select_contributed_session.png)

### Exploring Available Applications

Once you've selected the contributed session type, the container dropdown reveals the current catalogue of available applications. This list evolves as new applications are contributed and existing ones are updated.

![Choose Contributed App](images/contributed/2_select_contributed_container.png)

**Currently Available Applications:**

- **Marimo** (`images.canfar.net/cadc/marimo:latest`): Reactive Python notebooks, stored as pure Python files for easy version control and sharing.
- **VSCode Browser** (`images.canfar.net/cadc/vscode:latest`): Full Visual Studio Code experience in your browser, ideal for software development and complex analyses.


 As the community develops new tools and contributes them to the platform, the available applications expand to meet emerging research needs. If you have ideas for applications that would benefit the astronomy community, the CANFAR team encourages you to reach out to [support@canfar.net](mailto:support@canfar.net).

### Configuring Your Session

#### Choosing a Meaningful Name

When setting up your contributed application session, choose a name that reflects both the application and the purpose of your work. For example: `marimo-pipeline-development`, or `vscode-survey-processing`.

![Name Contributed Session](images/contributed/3_choose_contributed_name.png)

### Launching and Connecting

After configuring your session parameters, clicking "Launch" initiates the container deployment process. The session will appear on your portal dashboard, and you can monitor its startup progress. Contributed applications typically take 30-90 seconds to fully initialize, as they need to start the web service and establish connections to CANFAR's storage systems.

Once the session is running, clicking the session icon will open the application in a new browser tab. The first connection might take a few additional moments as the application completes its startup sequence and presents its interface.

![Launch Contributed Session](images/contributed/5_launch_contributed.png)

## 🔧 Working Effectively

### Understanding Application Interfaces

Most contributed applications follow modern web application conventions, but each has its own personality and workflow patterns. Rather than trying to force a one-size-fits-all approach, take some time to explore each application's unique features and interface paradigms.

The typical structure you'll encounter includes a navigation or menu area that provides access to the application's main features, a central content area where your work happens, and various panels or sidebars for configuration, file management, and tool access. Status information and feedback usually appear in designated areas that don't interfere with your primary workflow.

### Integrating with CANFAR Storage

!!! warning "Persistence Reminder"
    Save important results to `/arc/projects/[project]` or `/arc/home/[user]`. Temporary paths and in-app caches may not persist after the session ends.

One of the  aspects of contributed applications is their seamless integration with CANFAR storage infrastructure. Your applications can directly access your project data through `/arc/projects/[project]/`, your personal files via `/arc/home/[user]/`, and temporary processing space in `/scratch/`. This integration means you can move fluidly between different types of sessions and applications while maintaining access to the same data.

Understanding these storage patterns helps you organise your work effectively. You might use your personal home directory for notebooks and scripts under development, project directories for shared data and collaborative work, and scratch space for temporary files and intermediate processing results that don't need long-term storage.

### Authentication and Collaboration

The integration with CANFAR's authentication system means you don't need to manage separate credentials for each application. Your existing CANFAR account provides access to all contributed applications, and the same group-based permissions that govern your access to shared storage also apply within applications.

## 🛠️ Real-World Examples

### Collaborative Development with VSCode Browser

Consider a scenario where you are collaborating with colleagues on a complex data processing pipeline that involves multiple Python modules, configuration files, and documentation. Using VSCode Browser, you can work in a full-featured development environment that includes syntax highlighting, debugging capabilities, integrated terminal access, and extension support for specialized astronomical tools.

The browser-based nature means your collaborators can access the same development environment without worrying about local software installation or version compatibility issues. Everyone works with the same tools, the same Python environment, and the same file system, eliminating the "works on my machine" problem that often plagues collaborative software development.

### Modern Python Notebooks with Marimo

If you have experienced frustration with traditional Jupyter notebooks becoming inconsistent as you develop and modify your analysis, Marimo offers a modern alternative. Because Marimo notebooks are reactive and stored as standard Python files, you can develop complex analyses that remain consistent and reproducible.

The reactive execution model means that when you modify a function or variable definition, all dependent computations automatically update. This eliminates the common notebook problem where cells are executed out of order, leaving you with inconsistent results. The fact that notebooks are stored as Python files also makes them easy to version control with Git and share with colleagues who might not be using notebook environments.

## 🔒 Best Practices

### Understanding Application Permissions

Contributed applications operate within the same security framework as other CANFAR services, inheriting your account permissions and access controls. This means they can access your home directory, project directories on `/arc/`  you are a member of, and vault VOSpace areas where you have appropriate permissions. However, they cannot access other users private data or perform system administration functions at run time.

When working with contributed applications, it's important to understand what data the application might access and how it processes that information. Most applications are designed to work locally with your data and don't transmit information to external services, but it's always good practice to review the documentation for any application you're using for the first time.

## 🧑‍💻 Contributing Your Apps

### Understanding the Technical Framework

If you're interested in developing your own contributed application, the technical requirements are designed to be straightforward while ensuring security and compatibility with CANFAR's infrastructure. Your application needs to be containerized and provide a web interface that runs on port 5000.

The key technical requirement is including a startup script at `/skaha/startup.sh` in your container image. This script serves as the entry point for your application and should handle the initialization and startup of your web service. Here's how this typically works in practice:

```dockerfile
# Expose the required port
EXPOSE 5000

# Create the skaha directory and copy your startup script
RUN mkdir /skaha
COPY your_startup_script.sh /skaha/startup.sh
RUN chmod gou+x /skaha/startup.sh

# Set the startup script as the entrypoint
ENTRYPOINT [ "/skaha/startup.sh" ]
```

Your startup script needs to launch your web application in a way that handles signals properly and listens on the correct interface. Here's the pattern used by the Marimo application:

```bash
#!/bin/bash -e
set -e
echo "[Application Startup] Starting application server..."

# Use 'exec' to replace the script process with your application process.
# This is important for signal handling (e.g., SIGTERM from Kubernetes).
exec your_application \
  --port 5000 \
  --host 0.0.0.0 \
  --other-required-options
```

The `exec` command is crucial because it ensures proper signal handling when the container needs to shut down. The `--host 0.0.0.0` flag makes your application accessible from outside the container, and `--port 5000` uses the standard port that CANFAR expects.

### Development and Testing Workflow

Developing a contributed application typically follows an iterative process. You'll start by building and testing your application locally using Docker, ensuring it works correctly in a containerized environment. Once you have a working container, you can test it on CANFAR by pushing it to a container registry and launching it as a contributed application session.

During development, pay particular attention to how your application integrates with CANFAR storage systems and authentication. Test that your application can access the expected file system paths and that it behaves correctly when running under the CANFAR user account rather than as root.

### Community Integration

The most successful contributed applications solve real problems that multiple researchers face and provide capabilities that aren't easily replicated with existing tools. Before beginning development, consider reaching out to the CANFAR community through the support channels to discuss your ideas and gather feedback on potential use cases.

When you are ready to contribute your application, contact [support@canfar.net](mailto:support@canfar.net) with information about your application's purpose, target user community, and key features. The CANFAR team will work with you to integrate your application into the platform and ensure it meets the technical and security requirements.

## 🆘 Troubleshooting

### Application Startup Problems

If your contributed application doesn't load or seems to hang during startup, the most common cause is that the application is still initializing. Web applications can take 60-90 seconds to fully start up, especially if they need to install packages or perform initial configuration. Try waiting a bit longer before concluding there's a problem.

Browser caching can sometimes cause issues with contributed applications, especially if you've used the same application before and it has been updated. Try refreshing the page or opening the application in a private/incognito browser window to bypass potential caching issues.

### Data Access Challenges

Problems accessing data usually stem from incorrect file paths or permission issues. Verify that the files you're trying to access exist in the expected locations and that you have the necessary permissions. Remember that contributed applications access the same file system as other CANFAR sessions, so paths that work in Jupyter notebooks should work in contributed applications as well.

If you're having trouble accessing shared project data, check your group membership and ensure that the project directory has the correct permissions. Sometimes data access issues are actually authentication problems in disguise.

## 📚 Evolving Ecosystem

### Current Applications and Their Strengths

The current catalogue of contributed applications represents different approaches to interactive scientific computing, each with its own strengths and ideal use cases.  Marimo brings similar reactive capabilities to Python while maintaining compatibility with standard Python tooling and version control systems. VSCode Browser provides the most comprehensive development environment, making it ideal for complex software projects, multi-file analyses, and situations where you need advanced editing capabilities or specific extensions. It's particularly valuable when you're developing tools that others will use or when you need the debugging and profiling capabilities that come with a full IDE.

### Looking Forward

The contributed applications ecosystem continues to evolve as the community identifies new needs and develops innovative solutions. Future applications might focus on specialized domains like time-series analysis, interactive 3D visualization, or collaborative annotation tools. The flexibility of the platform means that if you can envision a web-based tool that would benefit astronomical research, it can likely be implemented as a contributed application.

The key to this ecosystem's success is community engagement. As more researchers use these tools and provide feedback, applications improve and new ideas emerge. If you have suggestions for improvements to existing applications or ideas for entirely new tools, the CANFAR team encourages you to share them.

## 🔗 Research Integration

### Building Comprehensive Workflows

Contributed applications work best when integrated into comprehensive research workflows that leverage CANFAR's full capabilities. You might begin analysis in a Jupyter notebook session, move to a contributed application for specialized processing or visualization, and then return to notebooks for final analysis and documentation.

The seamless access to shared storage means you can hand off work between different session types and applications without worrying about data transfer or synchronization. This flexibility allows you to choose the best tool for each phase of your research rather than being constrained by the limitations of any single environment.

### Collaboration and Knowledge Sharing

The web-based nature of contributed applications makes them particularly powerful for collaboration and knowledge sharing. You can share session URLs with colleagues for real-time collaboration, use the same applications for training workshops and educational activities, and ensure that everyone on your team has access to the same tools and capabilities regardless of their local computing environment.

This democratization of access to specialized tools can significantly impact how research teams work together and how knowledge is transferred between experienced and novice researchers.

## 🔗 What's Next?

Contributed applications represent just one facet of CANFAR's comprehensive research platform. To make the most of these tools, consider exploring how they integrate with CANFAR's other capabilities. The [Storage Guide](../storage/index.md) will help you effectively manage data for use with contributed applications. Understanding [Notebook Sessions](notebook.md) can help you prepare data for specialized processing in contributed applications. For automated workflows, [Batch Processing](batch.md) can complement the interactive analysis you do in contributed applications. And if you're interested in developing your own tools, the [Container Development](../containers/build.md) guide provides the technical foundation for creating contributed applications.

---

!!! tip "Making the Most of Contributed Applications"
    The key to success with contributed applications lies in matching the right tool to your specific workflow needs. Take time to explore each application's unique capabilities, don't hesitate to experiment with different approaches to your analysis challenges, and remember that the most powerful workflows often combine multiple tools and session types. The CANFAR community is always eager to help you find the best approaches for your research, so don't hesitate to reach out with questions or suggestions.
