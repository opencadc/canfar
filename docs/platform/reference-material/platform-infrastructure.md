# 🏗️ CANFAR Science Platform Infrastructure

Technical documentation and infrastructure details for the CANFAR Science Platform.

## 📋 Overview

The **CANFAR Science Platform** is built on a modern, cloud-native architecture designed to provide scalable, reliable access to astronomical computing resources. The platform combines container orchestration, distributed storage, and web-based interfaces to support a wide range of scientific workflows.

## 🔧 Core Infrastructure Components

### Container Orchestration
- **Kubernetes**: Manages container deployment and scaling
- **Skaha**: CANFAR's custom session management service
- **Docker Registry**: Stores and distributes container images
- **Load Balancing**: Distributes user sessions across compute nodes

### Storage Systems
- **POSIX Storage**: High-performance parallel file system for `/arc/projects`
- **VOSpace**: Web-accessible object storage for data sharing
- **Persistent Volumes**: Container session storage management
- **Backup Systems**: Automated data protection and recovery

### Authentication & Authorization
- **CADC Authentication**: Integration with Canadian Astronomy Data Centre
- **OIDC/OAuth2**: Modern authentication protocols
- **Group Management**: Role-based access control
- **API Tokens**: Programmatic access authentication

### Web Services
- **Science Portal**: Main user interface at [www.canfar.net](https://www.canfar.net)
- **REST APIs**: Programmatic platform access
- **Proxy Services**: Secure access to user sessions
- **Monitoring**: Platform health and performance tracking

---

## 🛠️ Development and Deployment

### Source Code Repository
The complete platform infrastructure and deployment configuration is maintained at:

**[github.com/opencadc/science-platform](https://github.com/opencadc/science-platform)**

This repository contains:
- Kubernetes deployment manifests
- Service configuration files
- Container image definitions
- Documentation and deployment guides
- Infrastructure as code templates

### Architecture Components

```text
┌─────────────────────────────────────────────────────────────┐
│                    CANFAR Science Platform                  │
├─────────────────────────────────────────────────────────────┤
│  Web Portal    │  REST APIs    │  Authentication Service    │
├─────────────────────────────────────────────────────────────┤
│         Skaha Session Management Service                    │
├─────────────────────────────────────────────────────────────┤
│              Kubernetes Container Orchestration             │
├─────────────────────────────────────────────────────────────┤
│  Compute Nodes  │  Storage Systems  │  Network Infrastructure │
└─────────────────────────────────────────────────────────────┘
```

### Key Services

**Skaha Service**: 
- Session lifecycle management
- Resource allocation and monitoring  
- Container image registry integration
- User session proxying

**Portal Service**:
- Web-based user interface
- Session launcher and management
- File browser and data transfer
- Group and permission management

**Storage Service**:
- POSIX-compliant shared storage
- VOSpace object storage
- Data transfer and synchronization
- Backup and archival systems

---

## 🔍 Technical Specifications

### Compute Resources
- **CPU**: Intel Xeon processors with AVX512 support
- **Memory**: Up to 1TB RAM per node
- **Storage**: NVMe SSD local storage + shared network storage
- **GPU**: NVIDIA A100 and V100 accelerators (limited availability)

### Network Infrastructure
- **Bandwidth**: 100 Gbps network backbone
- **Latency**: Sub-millisecond internal communication
- **External**: Multiple 10 Gbps external connections
- **Security**: Network segmentation and firewall protection

### Software Stack
- **Operating System**: Ubuntu Linux LTS
- **Container Runtime**: containerd with Docker compatibility
- **Orchestration**: Kubernetes 1.25+
- **Storage**: Ceph distributed storage system
- **Monitoring**: Prometheus + Grafana observability stack

---

## 📊 Monitoring and Observability

### Platform Metrics
- **Resource utilization**: CPU, memory, storage consumption
- **Session metrics**: Active users, session duration, resource usage
- **Performance**: Response times, throughput, error rates
- **Capacity planning**: Growth trends and resource forecasting

### Health Monitoring
- **Service availability**: 24/7 automated monitoring
- **Performance dashboards**: Real-time platform metrics
- **Alert systems**: Proactive issue detection and notification
- **Maintenance windows**: Scheduled updates and maintenance

---

## 🔒 Security and Compliance

### Security Measures
- **Network isolation**: Segmented networks for different services
- **Container security**: Image scanning and runtime protection
- **Access controls**: Multi-factor authentication and authorization
- **Data encryption**: At-rest and in-transit data protection

### Compliance
- **Data governance**: Canadian data residency requirements
- **Privacy protection**: PIPEDA compliance for personal data
- **Research ethics**: Institutional research ethics board alignment
- **International standards**: ISO 27001 security practices

---

## 🚀 Contributing to Platform Development

### Getting Involved
- **Issue tracking**: [GitHub Issues](https://github.com/opencadc/science-platform/issues)
- **Development discussion**: [OpenCADC Slack](https://opencadc.slack.com)
- **Documentation**: [Platform documentation](https://github.com/opencadc/science-platform/wiki)
- **Code contributions**: Pull requests welcome

### Development Environment
- **Local testing**: Minikube-based development setup
- **Staging environment**: Pre-production testing platform
- **Continuous integration**: Automated testing and deployment
- **Code review**: Peer review process for all changes

### Support Resources
- **Technical documentation**: [OpenCADC documentation](https://www.opencadc.org)
- **Developer community**: Active Slack and GitHub communities
- **Training materials**: Platform development guides and tutorials
- **Expert consultation**: Connect with CANFAR platform team

![CANFAR](https://www.canfar.net/css/images/logo.png){ height="200" }
