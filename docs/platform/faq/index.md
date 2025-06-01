# Frequently Asked Questions

This section answers common questions about using the CANFAR Science Platform, from basic usage to advanced troubleshooting.

## Getting Started

### How do I get access to CANFAR?

1. **Request an account**: Visit [canfar.net](https://canfar.net) and click "Request Account"
2. **Provide justification**: Explain your research needs and institutional affiliation
3. **Wait for approval**: Account approval typically takes 1-2 business days
4. **Join a group**: Contact your project PI to be added to relevant research groups

### What's the difference between the session types?

| Session Type | Best For | Resources | GUI |
|--------------|----------|-----------|-----|
| **Notebook** | Interactive analysis, prototyping | Low-Medium | Jupyter Lab |
| **Desktop** | GUI applications, multi-app workflows | Medium-High | Full Linux desktop |
| **CARTA** | Image/cube visualization | Medium | Specialized viewer |
| **Headless** | Batch processing, automation | Variable | None (API only) |

### How much does it cost to use CANFAR?

CANFAR is **free for academic research**. The platform is funded by the Canadian government and partner institutions to support astronomical research. Commercial users may have different arrangements.

## Account and Access

### I forgot my password. How do I reset it?

CANFAR uses **certificate-based authentication**, not passwords. If you're having login issues:

1. Check that your browser certificate is properly installed
2. Try a different browser
3. Contact [support@canfar.net](mailto:support@canfar.net) for certificate reissue

### How do I join a research group?

Groups control access to shared storage and resources:

1. **Contact the group PI**: Ask to be added to the relevant project group
2. **Provide your CANFAR username**: Usually your email address
3. **Wait for approval**: PIs can add members through the Science Portal

### Can I access CANFAR from anywhere in the world?

Yes, CANFAR is accessible from anywhere with internet access. However, large data transfers may be faster from Canadian institutions due to network proximity.

## Storage and Data

### How much storage do I get?

Storage allocation depends on your groups:

- **Personal space**: 10GB in `/arc/home/[username]/`
- **Group storage**: Varies by project, typically 100GB to several TB
- **Temporary storage**: Unlimited in `/tmp/` (cleared when session ends)

### Where should I put my data?

Follow this storage strategy:

- **Raw data**: `/arc/projects/[group]/raw/` - Original, unmodified observations
- **Working data**: `/arc/projects/[group]/data/` - Data being actively processed
- **Results**: `/arc/projects/[group]/results/` - Final analysis outputs
- **Scripts**: `/arc/projects/[group]/scripts/` - Analysis code and pipelines
- **Personal work**: `/arc/home/[username]/` - Individual analysis and notes

### How do I transfer large datasets?

For datasets larger than a few GB:

**From external sources**:
```bash
# Use rsync for resumable transfers
rsync -avz --progress source/ username@canfar.net:/arc/projects/mygroup/

# For very large files, use VOSpace
cadc-data put largefile.fits vos:myproject/data/
```

**To/from CANFAR**:
- Use the Science Portal file manager for files <1GB
- Use command-line tools (`rsync`, `scp`) for larger transfers
- Use VOSpace for files >10GB

### What file formats are supported?

CANFAR supports all standard astronomical formats:

- **FITS**: Standard astronomical images and tables
- **HDF5**: Large datasets and modern archives
- **CASA formats**: Measurement sets and images
- **Text formats**: CSV, ASCII tables, JSON
- **Images**: PNG, JPEG, PDF for plots and figures

## Sessions and Computing

### How long can my session run?

**Interactive sessions**:
- Maximum 7 days of continuous runtime
- Automatic shutdown after 24 hours of inactivity
- Can be resumed if not explicitly deleted

**Batch jobs**:
- No strict time limits
- Queue priority depends on resource usage
- Long jobs (>24 hours) may have lower priority

### My session won't start. What should I do?

Common causes and solutions:

**Resource constraints**:
- Try reducing memory or CPU requirements
- Check resource availability in the Science Portal
- Consider running during off-peak hours (evenings, weekends)

**Container issues**:
- Verify the container name is correct
- Try a different container version
- Check if the container is deprecated

**Account problems**:
- Verify you're in the correct groups
- Check that your account is active
- Contact support if needed

### Can I run GPU-accelerated applications?

Yes, CANFAR provides GPU resources for supported workloads:

**Available GPUs**:
- NVIDIA Tesla V100: Machine learning, deep learning
- NVIDIA RTX series: General GPU computing
- Limited availability - request in session configuration

**Common GPU applications**:
- TensorFlow and PyTorch for machine learning
- CUDA-accelerated astronomy codes
- Image processing and computer vision

**Requesting GPU access**:
1. Select "GPU" in session configuration
2. Choose appropriate GPU type
3. Ensure your container supports GPU computing

### How do I monitor my resource usage?

**In interactive sessions**:
```bash
# Check memory usage
free -h

# Monitor CPU usage
htop

# Check disk usage
df -h

# Monitor GPU usage (if applicable)
nvidia-smi
```

**Through the Science Portal**:
- View active sessions and their resource consumption
- Monitor group storage usage
- Track session history and runtime

## Software and Containers

### What software is available?

CANFAR provides containers with pre-installed software:

**General astronomy**:
- **astroml**: Modern Python astronomy stack (AstroPy, NumPy, SciPy, Matplotlib)
- **General purpose**: Basic Python data science tools

**Specialized tools**:
- **CASA**: Radio astronomy data reduction
- **CARTA**: Image and data cube visualization
- **DS9**: FITS image viewer
- **TOPCAT**: Table analysis and visualization

**Development environments**:
- **Jupyter**: Interactive notebooks
- **Linux desktop**: Full graphical environment
- **Custom containers**: Build your own software stacks

### Can I install additional software?

**In existing containers**:
```bash
# Install Python packages (temporary)
pip install --user package_name

# Install system packages (if you have sudo access)
sudo apt-get install package_name
```

**Permanent installations**:
- Build custom containers with your software stack
- See the [Container Guide](../user-guide/containers/index.md) for details

### How do I update to newer software versions?

**Container updates**:
- CANFAR regularly updates container images
- New versions appear in the session creation menu
- Older versions remain available for compatibility

**Manual updates**:
```bash
# Update Python packages
pip install --upgrade --user package_name

# Update conda environments (if applicable)
conda update --all
```

## Collaboration and Sharing

### How do I share my work with collaborators?

**Session sharing**:
1. In your active session, access the sharing menu
2. Add collaborator usernames
3. Set permissions (view-only or full access)
4. Collaborators can join your session in real-time

**Data sharing**:
- Add collaborators to your project group
- Use shared group storage in `/arc/projects/[group]/`
- Set appropriate file permissions

**Code sharing**:
- Use Git repositories for version control
- Share Jupyter notebooks through group storage
- Document your analysis workflows

### Can multiple people use the same session?

Yes, interactive sessions support real-time collaboration:

- **Shared desktop**: Multiple users can see and control the same desktop
- **Jupyter sharing**: Collaborative notebook editing
- **CARTA sharing**: Synchronized image viewing and analysis

### How do I cite CANFAR in my publications?

Include this acknowledgment in your papers:

> "This research made use of the CANFAR computing facility, which is managed by the National Research Council of Canada and funded by the Canadian Space Agency."

For more detailed citation information, see [canfar.net/citation](https://canfar.net/citation).

## Troubleshooting

### My analysis is running slowly. How can I speed it up?

**Check resource usage**:
```bash
# Monitor system resources
htop
iotop  # Disk I/O
```

**Optimization strategies**:

1. **Use scratch storage**: Process data in `/tmp/` for faster I/O
2. **Increase resources**: Request more memory or CPU cores
3. **Optimize code**: Use vectorized operations, efficient algorithms
4. **Parallel processing**: Utilize multiple cores when possible
5. **Data locality**: Keep frequently accessed data in fast storage

### I'm getting "out of memory" errors. What should I do?

**Immediate solutions**:
- Close unnecessary applications
- Clear Python/CASA cache
- Process data in smaller chunks

**Long-term solutions**:
- Request more memory for your session
- Optimize your analysis to use less memory
- Use memory-mapped file access for large datasets

### My container won't start or crashes immediately. Help!

**Diagnostic steps**:

1. **Check container logs**: Look for error messages in session logs
2. **Try different container**: Test with a basic container (e.g., astroml)
3. **Reduce resources**: Start with minimal memory/CPU requirements
4. **Check group permissions**: Ensure you have access to required storage

**Common fixes**:
- Update browser to latest version
- Clear browser cache and cookies
- Try incognito/private browsing mode
- Check network connectivity

### I can't access my files. Where did they go?

**Check common locations**:
```bash
# Personal storage
ls /arc/home/$(whoami)/

# Group storage
ls /arc/projects/

# Temporary files (session-specific)
ls /tmp/
ls ~/
```

**File recovery**:
- Files in `/tmp/` are deleted when sessions end
- Files in `/arc/` storage are persistent
- Contact support for backup restoration if needed

### Browser issues and compatibility

**Supported browsers**:
- **Chrome/Chromium**: Best compatibility and performance
- **Firefox**: Good compatibility
- **Safari**: Limited support, some features may not work
- **Edge**: Basic support

**Common browser fixes**:
- Enable cookies and JavaScript
- Disable ad blockers for canfar.net
- Clear browser cache and cookies
- Update browser to latest version

## Advanced Usage

### Can I run my own Docker containers?

Yes, you can build and use custom containers:

1. **Build locally**: Create your Dockerfile with required software
2. **Push to Harbor**: Upload to CANFAR's container registry
3. **Use in sessions**: Select your custom container in session creation

See the [Container Development Guide](../user-guide/containers/index.md) for detailed instructions.

### How do I automate workflows with the API?

CANFAR provides REST APIs for programmatic access:

```python
import requests

# Submit a batch job
response = requests.post(
    "https://ws-uv.canfar.net/skaha/v0/session",
    headers={"Authorization": f"Bearer {token}"},
    data={
        "name": "automated-analysis",
        "image": "images.canfar.net/skaha/astroml:latest",
        "cores": 4,
        "ram": 16,
        "kind": "headless",
        "cmd": "python /arc/projects/myproject/analyze.py"
    }
)
```

### Can I connect external tools to CANFAR?

**SSHFS mounting**:
```bash
# Mount CANFAR storage locally
sshfs username@canfar.net:/arc/projects/mygroup/ ~/canfar_mount/
```

**VOSpace access**:
```python
# Access VOSpace programmatically
from cadcdata import CadcDataClient

client = CadcDataClient()
client.put_file("local_file.fits", "vos:myproject/data/file.fits")
```

## Performance Tips

### General optimization

1. **Choose appropriate resources**: Don't over-request CPU/memory
2. **Use scratch storage**: Process data in `/tmp/` for speed
3. **Monitor usage**: Keep an eye on resource consumption
4. **Clean up**: Remove temporary files regularly
5. **Work during off-peak**: Better performance evenings/weekends

### For large datasets

1. **Stream processing**: Process data in chunks rather than loading entirely
2. **Parallel processing**: Use multiple cores effectively
3. **Memory mapping**: Use memory-mapped file access
4. **Compression**: Compress intermediate results to save I/O
5. **Batch operations**: Group similar operations together

### For collaborative work

1. **Coordinate resource usage**: Avoid competing for resources
2. **Share efficiently**: Use read-only sharing when possible
3. **Document workflows**: Clear documentation helps collaboration
4. **Version control**: Use Git for shared code development

## Getting Help

### Self-help resources

- **Documentation**: Browse the [User Guide](../user-guide/index.md)
- **Radio Astronomy**: Check [radio astronomy guide](../user-guide/radio-astronomy/index.md) for specialized workflows
- **Community**: Join our Discord for peer support
- **Examples**: Look at example notebooks and scripts

### Contacting support

**Email**: [support@canfar.net](mailto:support@canfar.net)

**Include in your support request**:
- Your CANFAR username
- Description of the problem
- Steps to reproduce the issue
- Error messages (copy/paste exact text)
- Session type and container used

**Response time**: Support typically responds within 1-2 business days.

### Community support

**Discord community**: Join our Discord server for:
- Quick questions and answers
- Tips and tricks sharing
- Collaboration opportunities
- Announcements of new features

**Office hours**: Weekly virtual office hours for real-time help (check Discord for schedule).

## Feature Requests and Feedback

### Suggesting improvements

We welcome feedback and suggestions:

- **Feature requests**: Email specific ideas to support
- **Bug reports**: Include detailed reproduction steps
- **Documentation**: Suggest improvements or missing topics
- **Software requests**: Request additional containers or software

### Contributing to CANFAR

- **Documentation**: Help improve these docs (see [Contributing Guide](../help/index.md#contributing-to-documentation))
- **Containers**: Share useful container recipes
- **Tutorials**: Create tutorials for your research area
- **Testing**: Help test new features in beta

Your feedback helps make CANFAR better for the entire astronomy community!
