# Launching Contributed Applications

**Access community-developed tools and specialized research applications**

!!! abstract "🎯 What You'll Learn"
    - What contributed applications are and when to use them
    - How to launch and size contributed application sessions
    - How these apps integrate with CANFAR storage and authentication
    - Best practices for collaboration, performance, and security

Contributed applications represent an exciting expansion of CANFAR's capabilities beyond the standard notebook and desktop environments. These specialized tools have been developed by the CANFAR community and external collaborators to address specific astronomical workflows and research needs that aren't well-served by conventional interfaces.

## 🎯 Contributed Apps

Think of contributed applications as purpose-built web tools that seamlessly integrate with CANFAR's infrastructure while offering unique capabilities. Unlike the general-purpose notebook or desktop sessions you might be familiar with, these applications are crafted for specific tasks and often provide interfaces that would be difficult or impossible to replicate in standard environments.

These applications extend CANFAR's reach by providing specialized interfaces for targeted research tasks, integrating naturally with CANFAR's storage and authentication systems, and offering workflows that leverage the unique aspects of web-based scientific computing. What makes them particularly valuable is how they support community innovation and enable researchers to share specialized tools with colleagues worldwide.

### The Landscape of Contributed Applications

!!! info "Current Ecosystem"
    The catalog evolves regularly. Expect reactive notebooks (Pluto.jl, Marimo), browser IDEs (VSCode), and specialized computational interfaces contributed by the community.

The current ecosystem of contributed applications focuses on interactive computing environments that offer alternatives to traditional Jupyter notebooks. You'll find reactive notebook systems that provide real-time feedback as you modify code, browser-based development environments that give you the full power of modern IDEs without local installation, and specialized computational interfaces designed for specific programming languages or workflows.

Rather than trying to be everything to everyone, each contributed application excels in its particular domain. This focused approach means you can choose the tool that best matches your specific research workflow, whether you're doing exploratory data analysis, developing complex algorithms, or collaborating on code with distributed teams.

## 🚀 Getting Started

### Accessing the Application Catalog

Beginning your journey with contributed applications starts just like any other CANFAR session. After logging into the [CANFAR Science Portal](https://www.canfar.net), you'll click the familiar plus sign (**+**) to create a new session. The key difference comes when you select `contributed` as your session type, which opens up the specialized application catalog.

![Select Contributed Session](images/contributed/1_select_contributed_session.png)

### Exploring Available Applications

Once you've selected the contributed session type, the container dropdown reveals the current catalog of available applications. This list represents the cutting edge of community-developed tools, and it evolves as new applications are contributed and existing ones are updated.

![Choose Contributed App](images/contributed/2_select_contributed_container.png)

**Currently Available Applications:**

**Pluto.jl** (`images.canfar.net/skaha/pluto:latest`) offers a revolutionary approach to Julia programming through reactive notebooks. Unlike traditional notebook environments where cells execute in sequence, Pluto creates a dynamic environment where changing any variable automatically updates all dependent computations throughout the notebook. This makes it exceptionally powerful for exploratory data analysis and interactive visualization.

**Marimo** (`images.canfar.net/skaha/marimo:latest`) brings reactive computing to Python, offering a modern alternative to Jupyter notebooks. Marimo notebooks are stored as pure Python files, making them easy to version control and share. The reactive execution model ensures your notebook stays consistent as you develop and modify your analysis.

**VSCode Browser** (`images.canfar.net/skaha/code-browser:latest`) provides the full Visual Studio Code experience directly in your web browser. This application is particularly valuable for software development projects, complex multi-file analyses, and situations where you need the rich editing capabilities and extensions ecosystem that VSCode provides.

!!! tip "Session Sizing"
    Start with 16GB RAM and 2-4 CPU cores for most contributed apps. Increase memory for large datasets or memory-intensive reactive notebooks.

The beauty of this system lies in its dynamic nature. As the community develops new tools and contributes them to the platform, the available applications expand to meet emerging research needs. If you have ideas for applications that would benefit the astronomy community, the CANFAR team encourages you to reach out to [support@canfar.net](mailto:support@canfar.net).

### Configuring Your Session

#### Choosing a Meaningful Name

When setting up your contributed application session, choose a name that reflects both the application you're using and the purpose of your work. Names like `pluto-galaxy-analysis-2024`, `marimo-pipeline-development`, or `vscode-survey-processing` help you quickly identify the session's purpose when you return to your work later.

![Name Contributed Session](images/contributed/3_choose_contributed_name.png)

#### Resource Planning

The resource requirements for contributed applications can vary significantly depending on the nature of your work and the specific application you're using. Web-based development environments like VSCode Browser typically run comfortably with 8-16GB of memory and 2-4 CPU cores, while reactive notebook environments processing large datasets might benefit from 16-32GB of memory.

For memory allocation, consider starting with 16GB as a reasonable default for most contributed applications. If you're working with large datasets or computationally intensive visualizations, you might want to increase this to 32GB or more. The reactive nature of some applications means they might use more memory than traditional notebooks since they maintain the state of all computations simultaneously.

CPU requirements are generally modest for most contributed applications, with 2-4 cores being sufficient for typical workflows. However, if your work involves parallel processing or you're running multiple computational tasks simultaneously, additional cores can significantly improve performance.

![Configure Contributed Resources](images/contributed/4_choose_contributed_resources.png)

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
    Save important results to `/arc/projects/` or `/arc/home/`. Temporary paths and in-app caches may not persist after the session ends.

One of the most powerful aspects of contributed applications is their seamless integration with CANFAR's storage infrastructure. Your applications can directly access your project data through `/arc/projects/yourproject/`, your personal files via `/arc/home/yourusername/`, and temporary processing space in `/scratch/`. This integration means you can move fluidly between different types of sessions and applications while maintaining access to the same data.

Understanding these storage patterns helps you organize your work effectively. You might use your personal home directory for notebooks and scripts under development, project directories for shared data and collaborative work, and scratch space for temporary files and intermediate processing results that don't need long-term storage.

### Authentication and Collaboration

The integration with CANFAR's authentication system means you don't need to manage separate credentials for each application. Your existing CANFAR account provides access to all contributed applications, and the same group-based permissions that govern your access to shared storage also apply within applications.

This seamless authentication enables powerful collaboration patterns. You can share session URLs with collaborators who have appropriate permissions, work together in real-time on analysis projects, and maintain consistent access controls across different tools and workflows.

## 🛠️ Real-World Examples

### Interactive Data Exploration with Pluto.jl

Imagine you're working with a large astronomical catalog and want to explore correlations between different measured parameters. Traditional notebook approaches require you to re-run cells manually as you adjust parameters or add new visualizations. With Pluto.jl, you can create sliders and interactive controls that automatically update all dependent visualizations and calculations in real-time.

You might start by loading your catalog data and creating a basic scatter plot. As you add interactive controls for magnitude cuts, color selections, or coordinate ranges, the plot updates automatically. When you decide to add a histogram showing the distribution of selected objects, it immediately reflects your current filter settings. This reactive approach makes exploratory data analysis feel more like an interactive conversation with your data.

### Collaborative Development with VSCode Browser

Consider a scenario where you're collaborating with colleagues on a complex data processing pipeline that involves multiple Python modules, configuration files, and documentation. Using VSCode Browser, you can work in a full-featured development environment that includes syntax highlighting, debugging capabilities, integrated terminal access, and extension support for specialized astronomical tools.

The browser-based nature means your collaborators can access the same development environment without worrying about local software installation or version compatibility issues. Everyone works with the same tools, the same Python environment, and the same file system, eliminating the "works on my machine" problem that often plagues collaborative software development.

### Modern Python Notebooks with Marimo

If you've experienced frustration with traditional Jupyter notebooks becoming inconsistent as you develop and modify your analysis, Marimo offers a refreshing alternative. Because Marimo notebooks are reactive and stored as standard Python files, you can develop complex analyses that remain consistent and reproducible.

The reactive execution model means that when you modify a function or variable definition, all dependent computations automatically update. This eliminates the common notebook problem where cells are executed out of order, leaving you with inconsistent results. The fact that notebooks are stored as Python files also makes them easy to version control with Git and share with colleagues who might not be using notebook environments.

## 🔒 Best Practices

### Understanding Application Permissions

Contributed applications operate within the same security framework as other CANFAR services, inheriting your account permissions and access controls. This means they can access your home directory, project directories where you're a member, and VOSpace areas where you have appropriate permissions. However, they cannot access other users' private data or perform system administration functions.

When working with contributed applications, it's important to understand what data the application might access and how it processes that information. Most applications are designed to work locally with your data and don't transmit information to external services, but it's always good practice to review the documentation for any application you're using for the first time.

### Data Security Considerations

The web-based nature of contributed applications introduces some unique security considerations. Always use HTTPS connections when accessing applications, be cautious about uploading sensitive credentials or tokens to applications unless specifically required, and use CANFAR's group-based permissions to manage access to shared data appropriately.

For researchers working with sensitive or proprietary data, it's worth understanding how each application handles data processing and whether any information might be cached or logged. Most contributed applications are designed with these concerns in mind, but understanding the data flow helps you make informed decisions about which tools to use for different types of work.

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

During development, pay particular attention to how your application integrates with CANFAR's storage systems and authentication. Test that your application can access the expected file system paths and that it behaves correctly when running under the CANFAR user account rather than as root.

### Community Integration

The most successful contributed applications solve real problems that multiple researchers face and provide capabilities that aren't easily replicated with existing tools. Before beginning development, consider reaching out to the CANFAR community through the support channels to discuss your ideas and gather feedback on potential use cases.

When you're ready to contribute your application, contact [support@canfar.net](mailto:support@canfar.net) with information about your application's purpose, target user community, and key features. The CANFAR team will work with you to integrate your application into the platform and ensure it meets the technical and security requirements.

## 🆘 Troubleshooting

### Application Startup Problems

If your contributed application doesn't load or seems to hang during startup, the most common cause is that the application is still initializing. Web applications can take 60-90 seconds to fully start up, especially if they need to install packages or perform initial configuration. Try waiting a bit longer before concluding there's a problem.

Browser caching can sometimes cause issues with contributed applications, especially if you've used the same application before and it has been updated. Try refreshing the page or opening the application in a private/incognito browser window to bypass potential caching issues.

### Data Access Challenges

Problems accessing data usually stem from incorrect file paths or permission issues. Verify that the files you're trying to access exist in the expected locations and that you have the necessary permissions. Remember that contributed applications access the same file system as other CANFAR sessions, so paths that work in Jupyter notebooks should work in contributed applications as well.

If you're having trouble accessing shared project data, check your group membership and ensure that the project directory has the correct permissions. Sometimes data access issues are actually authentication problems in disguise.

### Performance and Resource Issues

If your contributed application feels slow or unresponsive, consider whether you've allocated sufficient resources for your workload. Web-based applications can be more memory-intensive than you might expect, especially reactive notebook environments that maintain state for all computations.

You can often improve performance by closing unnecessary browser tabs, ensuring you have sufficient memory allocated to your session, and monitoring your resource usage through the browser's developer tools if available.

## 📚 Evolving Ecosystem

### Current Applications and Their Strengths

The current catalog of contributed applications represents different approaches to interactive scientific computing, each with its own strengths and ideal use cases. Pluto.jl excels in situations where you want immediate feedback on how changes affect your analysis and is particularly powerful for teaching and exploration. Marimo brings similar reactive capabilities to Python while maintaining compatibility with standard Python tooling and version control systems.

VSCode Browser provides the most comprehensive development environment, making it ideal for complex software projects, multi-file analyses, and situations where you need advanced editing capabilities or specific extensions. It's particularly valuable when you're developing tools that others will use or when you need the debugging and profiling capabilities that come with a full IDE.

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

Contributed applications represent just one facet of CANFAR's comprehensive research platform. To make the most of these tools, consider exploring how they integrate with CANFAR's other capabilities. The [Storage Guide](../storage/index.md) will help you effectively manage data for use with contributed applications. Understanding [Notebook Sessions](launch-notebook.md) can help you prepare data for specialized processing in contributed applications. For automated workflows, [Batch Processing](../batch-jobs/index.md) can complement the interactive analysis you do in contributed applications. And if you're interested in developing your own tools, the [Container Development](../containers/index.md) guide provides the technical foundation for creating contributed applications.

---

!!! tip "Making the Most of Contributed Applications"
    The key to success with contributed applications lies in matching the right tool to your specific workflow needs. Take time to explore each application's unique capabilities, don't hesitate to experiment with different approaches to your analysis challenges, and remember that the most powerful workflows often combine multiple tools and session types. The CANFAR community is always eager to help you find the best approaches for your research, so don't hesitate to reach out with questions or suggestions.
