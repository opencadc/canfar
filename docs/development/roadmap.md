# CANFAR Development Roadmap

## Current Planning Increment (PI 28)

CANFAR-related work represents approximately 50% of development time during this increment.

### Priorities

- **Redundant registry deployments**: High-availability service registry infrastructure
- **Science Test Cases**: Detailed science verification workflows on CANFAR
- **Resource awareness improvements**: Better cluster resource awareness and configurability
- **GPU support on Portal**: User interface for GPU resource allocation
- **Cavern in SRCNet**: Integration with SRCNet Integration Environment
- **CANFAR Workshop** (TBD):
  - Part 1: Development and Operations
  - Part 2: User Training

## Strategic Roadmap

### Fair Share & Accounting

**Compute and I/O resource management**

- Implement fair-share scheduling algorithms
- Track and report resource usage per user/group
- Quota management and enforcement
- Billing/chargeback mechanisms (if applicable)

### Science Containers

**Container lifecycle and curation**

Current challenges:
- Harbor registry contains outdated and uncurated images
- Unclear ownership and maintenance responsibilities
- Need cleanup and better documentation

Roadmap items:
- Establish Harbor project organization guidelines
- Container curation and cleanup process
- Support for user-contributed containers
  - Define "contributed" container type
  - Quality and usefulness criteria
  - Maintenance model

### Software Delivery and Discovery

**CVMFS Integration**

- CVMFS-based software distribution
- Software discovery mechanisms for users
- Integration with existing CANFAR workflows

### Workflow Support

**Multi-framework workflow capabilities**

Support for popular workflow engines:
- Ray (distributed computing)
- Dask (parallel computing)
- Prefect (workflow orchestration)
- Other workflow frameworks as needed

Goals:
- Seamless integration with CANFAR sessions
- Resource management across workflow tasks
- Best practices documentation

### Large File Transfer

**High-performance data movement**

- **Globus integration**: High-speed file transfer service
- **NextCloud on /arc**: Web-based file access and sharing
- **External storage mounting**: FUSE-based access to external storage systems

### Python Client Improvements

**Unified Python ecosystem**

Goals:
- Consistent, integrated user experience across CADC tools
- Upstream contributions to:
  - PyVO (Virtual Observatory access)
  - Astroquery (astronomy data queries)
  - Astropy (core astronomy utilities)

### Monitoring and Observability

**Enhanced system visibility**

- Improved monitoring APIs
- User-facing resource usage dashboards
- System health metrics
- Performance analytics

### Portal Enhancements

**Science Portal feature roadmap**

Questions to address:
- Which backend services should be included?
- Which frontend applications belong in CANFAR?
- Balance between features and maintenance burden

### CANFAR-Next: Skaha API v2

**Next-generation API design**

Goals:
- Build new API model from ground up
- Resource specification with explicit units
- Modular API structure:
  - Separate `/image`, `/repo`, `/context` endpoints
  - Independent versioning per API module
- Backward compatibility strategy

Improvements:
- Clearer resource requests (CPU/memory with units)
- Better API documentation
- Improved error handling
- More RESTful design patterns

## Prioritization Process

### Stakeholder Involvement

Roadmap priorities are determined through:

1. **Users Committee**: Regular input from active CANFAR users
2. **Science Teams**: Requirements from research collaborations
3. **Operations Team**: Infrastructure and maintenance needs
4. **SRCNet Partners**: Multi-site deployment requirements

### Priority Criteria

Features are prioritized based on:

- **User Impact**: Number of users affected and severity of need
- **Strategic Value**: Alignment with long-term CANFAR goals
- **Technical Dependencies**: Prerequisites and blockers
- **Resource Availability**: Development capacity and expertise
- **Community Feedback**: User committee recommendations

## How to Influence the Roadmap

### For Users

- Participate in the users committee
- Provide feedback through the [CANFAR Discord](https://discord.gg/vcCQ8QBvBa)
- Submit feature requests via [GitHub Issues](https://github.com/opencadc/canfar/issues)
- Engage in [Discussions](https://github.com/opencadc/canfar/discussions)

### For Developers

- Attend planning meetings
- Propose features with use cases and implementation plans
- Contribute to architecture discussions
- Help with requirements gathering from user community

## Release Alignment

This roadmap is aligned with CANFAR's quarterly release cycle. Features are scheduled into releases based on:

- Completion status and testing
- Dependencies on other features
- User community readiness
- Documentation completeness

For specific release contents, see [release notes](../release-notes.md).
