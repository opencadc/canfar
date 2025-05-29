# 🌐 CANFAR Science Portal Administration

Comprehensive guide to the CANFAR Science Portal interfaces and administrative services.

## 📋 Portal Overview

The **CANFAR Science Portal** is the primary web interface for accessing and managing CANFAR services. Located at [www.canfar.net](https://www.canfar.net), it provides integrated access to computing resources, data management, collaboration tools, and administrative functions.

## 🚀 Main Portal Services

### Science Platform UI
**[Science Platform UI](https://www.canfar.net/science-portal)**

The main interface for launching and managing computing sessions.

**What it does**:
- Launch interactive computing sessions (Jupyter, Desktop, CARTA)
- Monitor active sessions and resource usage
- Browse and select from available container images
- Configure session parameters (CPU, memory, storage)

**How to use it**:
1. **Login** with your CADC credentials
2. **Choose session type**: Notebook, Desktop, or Headless
3. **Select container**: Pick the appropriate software environment
4. **Configure resources**: Set CPU cores, memory, and runtime limits
5. **Launch**: Start your computing session
6. **Connect**: Access your session through the provided link

**Key features**:
- Real-time session status monitoring
- Resource usage visualization
- Session history and logging
- Quick access to common containers
- Integration with storage systems

---

### Storage Management UI
**[Storage Management UI](https://www.canfar.net/storage/vault/list/)**

Web-based file management for both `vault` and `arc` storage systems.

**What it does**:
- Browse files and folders in your storage spaces
- Upload and download files through the web browser
- Manage file permissions and sharing
- Transfer data between different storage systems

**Storage Systems Available**:

#### Vault Storage (`/home/vault`)
- **Purpose**: Personal storage space for each user
- **Capacity**: Limited space for personal files and small datasets
- **Access**: Private to individual users by default
- **Best for**: Configuration files, scripts, small results

#### Arc Storage (`/arc/projects`)
- **Purpose**: Shared project storage for research groups
- **Capacity**: Large-scale storage for datasets and analysis results
- **Access**: Shared within research groups
- **Best for**: Large datasets, collaborative analysis, long-term storage

**File Management Features**:
- **Drag-and-drop uploads**: Easy file transfer from your computer
- **Folder creation**: Organize data with custom directory structures
- **Permission management**: Control access to files and folders
- **Download links**: Generate shareable links for data distribution
- **Bulk operations**: Select and manage multiple files simultaneously

**Tips for effective use**:
- Keep large datasets in `/arc/projects` for better performance
- Use descriptive folder names for project organization
- Regularly clean up temporary files to save storage space
- Set appropriate permissions for collaborative projects

---

### Group Management UI
**[Group Management UI](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/groups/)**

Administrative interface for managing research groups and collaborations.

**What it does**:
- Create and manage research groups
- Add and remove group members
- Set group permissions and access controls
- Configure project-specific settings

**Group Management Features**:

#### Creating Groups
1. **Navigate** to the Group Management interface
2. **Create group**: Click "Create New Group"
3. **Set details**: Provide group name, description, and purpose
4. **Configure permissions**: Set default access levels
5. **Add members**: Invite researchers to join the group

#### Managing Members
- **Member roles**: Assign different permission levels (admin, member, viewer)
- **Access control**: Grant or revoke access to specific resources
- **Collaboration tools**: Set up shared workspaces and data access
- **Activity monitoring**: Track group member activity and resource usage

#### Project Configuration
- **Storage allocation**: Request additional storage space for projects
- **Resource limits**: Set compute resource quotas for group members
- **Container access**: Control which software containers the group can use
- **Data sharing**: Configure external data sharing permissions

**Best practices**:
- Use descriptive group names that reflect research projects
- Regularly review and update group membership
- Set clear roles and responsibilities for group administrators
- Document group policies and data management practices

---

### DOI Publication Service
**[DOI Publication Service](https://www.canfar.net/citation)**

Service for publishing research datasets with Digital Object Identifiers (DOIs).

**What it does**:
- Generate permanent DOIs for research datasets
- Create citation-ready metadata for publications
- Integrate with research data repositories
- Support reproducible research practices

**Publication Process**:

#### Preparing Data for Publication
1. **Organize data**: Ensure datasets are well-organized and documented
2. **Add metadata**: Include descriptions, authorship, and technical details
3. **Quality check**: Verify data integrity and completeness
4. **Documentation**: Create README files and data dictionaries

#### Creating DOIs
1. **Select dataset**: Choose the data you want to publish
2. **Fill metadata**: Complete the DOI registration form
3. **Review information**: Check all details for accuracy
4. **Submit request**: Request DOI generation
5. **Receive DOI**: Get your permanent identifier for citations

**Metadata Requirements**:
- **Title**: Descriptive title for the dataset
- **Authors**: Complete author list with affiliations
- **Description**: Detailed description of the data and methodology
- **Keywords**: Relevant scientific keywords and topics
- **Technical details**: Data formats, software requirements, access methods

**Benefits of DOI publication**:
- **Permanent access**: Ensures long-term availability of research data
- **Proper citation**: Enables others to cite your datasets correctly
- **Research impact**: Increases visibility and reuse of your work
- **Funding compliance**: Meets data sharing requirements for grants
- **Reproducibility**: Supports open science and reproducible research

---

## 🔧 Administrative Tools

### Portal Configuration
- **User account management**: Profile settings and preferences
- **Session defaults**: Set preferred container images and resource configurations
- **Notification settings**: Configure alerts and email notifications
- **Integration settings**: Connect with external services and APIs

### Resource Monitoring
- **Usage dashboards**: Track your computing and storage resource consumption
- **Cost tracking**: Monitor resource costs and budget usage
- **Performance metrics**: View session performance and optimization opportunities
- **Historical data**: Access usage history and trends

### Collaboration Features
- **Shared workspaces**: Create collaborative computing environments
- **Data sharing**: Set up shared data access for research teams
- **Project management**: Organize resources by research project
- **Communication**: Integration with collaboration tools and messaging

---

## 🆘 Getting Help

### Support Resources
- **Portal documentation**: Built-in help and tutorials
- **User guides**: Step-by-step instructions for common tasks
- **Video tutorials**: Visual guides for portal features
- **FAQ section**: Answers to common questions

### Contact Support
- **Email support**: [support@canfar.net](mailto:support@canfar.net)
- **Slack community**: [CANFAR Slack](https://cadc.slack.com/archives/C01K60U5Q87)
- **Office hours**: Regular virtual support sessions
- **Training workshops**: Hands-on training for new users

### Troubleshooting
- **Session issues**: Problems with launching or connecting to sessions
- **Storage problems**: File upload/download and permission issues
- **Group management**: Adding members and configuring permissions
- **DOI publication**: Dataset preparation and metadata requirements

![CANFAR](https://www.canfar.net/css/images/logo.png){ height="200" }
