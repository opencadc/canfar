# CANFAR Release Process

## Current Release Cycle

CANFAR follows a **fixed, quarterly release cycle** to provide predictable updates and stable deployments.

## Current Practice: Edge Images

### Challenges with Fixed Releases

While quarterly releases provide stability, they present challenges for collaborations that need early access to features:

- **SRCNet Integration**: Updated components (cadc-registry, cavern, prepareData) need to be integrated before official release
- **Research Collaborations**: Some projects require pre-release access to new features

### Current Solution: Edge Image Tags

CANFAR currently uses a dual-track image tagging approach:

#### For Production Users

```bash
helm upgrade canfar opencadc/skaha
```

- Uses official helm charts pointing to release images (e.g., `skaha:1.0.2`)
- Gets latest stable release plus bug fixes only
- No access to unreleased features

#### For Early Adopters

To preview new features before official release, manually modify helm charts to use 'edge' images:

```yaml
image:
  repository: images.opencadc.org/platform/skaha
  tag: edge
```

This gives access to the latest development code for testing purposes.

## Future Enhancements Under Consideration

### Feature Flags / Feature Gates

**Status**: Planned, not yet implemented

A feature flag system would provide finer-grained control over new functionality:

1. **Development**: New feature code is merged to the "edge" branch with feature flags controlling activation
2. **Build**: Container image is built and published with the 'edge' tag
3. **Selective Enablement**: Deployers can enable specific features via environment variables:
   ```yaml
   env:
     - name: FEATURE_GPU_SUPPORT
       value: "true"
   ```
4. **Gradual Rollout**: Features can be tested in production without affecting all users
5. **Quick Rollback**: Problems can be addressed by disabling the flag without redeploying

This approach would support:
- Early access for collaborations (e.g., SRCNet) to specific features
- Safe testing of new functionality in production environments
- Quick rollback without code changes

### Release Branches

**Status**: Under evaluation

Considering the need for release branches across multiple repositories to better support:
- Bug fixes to production versions
- Multiple active release versions
- Coordinated releases across components

### Beta Program

**Status**: Proposed

A structured opt-in beta program could provide:
- Early testing access for interested users
- Feedback loop before general release
- Community involvement in quality assurance

## Retrospective: Lessons Learned

### Communication and Transparency

**Challenge**: Need more effective communication with users and communities

**Improvements**:
- Publish release dates and release notes early
- Maintain a public roadmap aligned with key stakeholders
- Create transparent descriptions of overall release goals
- Clearly communicate which features are in or out of each release
- Provide a forum for user discussion and feedback
- Engage external users early for testing and documentation review

### Testing and Deployment Strategy

**Challenge**: Different environments (keel-dev, canfar-b, prod) don't always behave identically

**Learnings**:
- **Multiple K8s clusters are essential** for different testing stages
- **Pre-deployment testing** on canfar-b proved valuable before production
- **Environment differences** between dev/staging/prod can cause unexpected bugs
- Need to clearly track what was released on each cluster

**Best Practices**:
- Use separate clusters for: development → staging (canfar-b) → production
- Document environment-specific configurations
- Test on staging environment that closely mirrors production

### Monitoring and Observability

**Challenge**: Insufficient visibility into release effectiveness and system health

**Improvements Needed**:
- Better monitoring and observability tools
- Confidence metrics for release success
- Proactive issue detection before user reports

### Feature Management

**Challenge**: Managing stakeholder expectations and conflicting feedback

**Solutions**:
- Establish clear acceptance criteria before development
- Reduce conflicting feedback from multiple story acceptors
- Involve community in feature prioritization
- Consider opt-in beta program for early testing

### Supporting Multiple Deployments

**Challenge**: Supporting alternate CANFAR deployments increases complexity

**Considerations**:
- Consistent naming conventions across GitHub repositories
- Clear documentation for deployment variations
- Balance between flexibility and maintenance burden

## Release Artifacts

### Helm Charts

Official helm charts are maintained in [opencadc/deployments](https://github.com/opencadc/deployments/tree/main/helm/applications/skaha)

### Container Images

- **Release images**: Tagged with semantic versions (e.g., `1.0.2`)
- **Edge images**: Tagged with `edge`, contain pre-release features
- Hosted at `images.opencadc.org/platform/`

### Python Client & CLI

Published to PyPI as the `canfar` package, following independent versioning.

## Contributing to Releases

### For Developers

1. Participate in planning meetings
2. Follow consistent documentation practices
3. Use feature flags for new functionality
4. Test on multiple environments before release

### For Deployers

1. Use official helm charts for production
2. Test edge features on non-production clusters
3. Provide feedback on pre-release functionality
4. Report environment-specific issues

