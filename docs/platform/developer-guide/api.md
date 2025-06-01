# API Access and Programmatic Control

Learn how to interact with CANFAR programmatically using REST APIs (Application Programming Interfaces) for automated session management and workflow integration.

## What is the Skaha API?

The **Skaha API** is a REST web service that provides programmatic access to CANFAR session management.
Instead of using the web portal manually, you can write scripts to:

- Launch and terminate computing sessions, including headless ones (jobs)
- Monitor session status and resource usage
- List available container images
- Manage session resources and configurations
- Automate complex scientific workflows

**API Base URL**: `https://ws-uv.canfar.net/skaha`
**API Documentation**: Complete technical reference available at the base URL

## Use Cases for API Access

- **Batch processing**: Submit multiple analysis jobs automatically
- **Workflow automation**: Chain analysis steps in complex pipelines
- **Resource monitoring**: Track usage across multiple projects
- **Custom interfaces**: Build specialized tools for your research group

---

## 🔑 Authentication

### Getting API Access
1. **Login to CANFAR**: [https://www.canfar.net](https://www.canfar.net)
2. **Generate token**: Go to your profile → API tokens
3. **Save credentials**: Store securely for programmatic access

### Using Authentication
```python
import requests

# Your API credentials
token = "your_api_token_here"
headers = {"Authorization": f"Bearer {token}"}

# API base URL
base_url = "https://ws-uv.canfar.net/skaha/v0"
```

---

## 📋 Session Management

### List Running Sessions
```python
# Get all your active sessions
response = requests.get(f"{base_url}/session", headers=headers)
sessions = response.json()

for session in sessions:
    print(f"ID: {session['sessionId']}")
    print(f"Type: {session['type']}")
    print(f"Status: {session['status']}")
    print(f"Image: {session['image']}")
    print("---")
```

### Launch a New Session
```python
# Launch a Jupyter notebook session
launch_data = {
    "name": "my-analysis-session",
    "image": "images.canfar.net/skaha/astroml:latest",
    "cores": 2,
    "ram": 4,  # GB
    "kind": "notebook"
}

response = requests.post(f"{base_url}/session", 
                        headers=headers, 
                        data=launch_data)
                        
if response.status_code == 200:
    session_info = response.json()
    print(f"Session launched: {session_info['sessionId']}")
    print(f"Connect URL: {session_info['connectURL']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Monitor Session Status
```python
def wait_for_session(session_id, timeout=300):
    """Wait for session to be ready"""
    import time
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.get(f"{base_url}/session/{session_id}", headers=headers)
        session = response.json()
        
        if session['status'] == 'Running':
            return session
        elif session['status'] == 'Error':
            raise Exception(f"Session failed: {session.get('statusMessage', 'Unknown error')}")
            
        time.sleep(10)  # Check every 10 seconds
    
    raise TimeoutError("Session did not start within timeout")

# Usage
session = wait_for_session("your_session_id")
print(f"Session ready at: {session['connectURL']}")
```

### Terminate Session
```python
# Stop a specific session
session_id = "your_session_id"
response = requests.delete(f"{base_url}/session/{session_id}", headers=headers)

if response.status_code == 200:
    print("Session terminated successfully")
else:
    print(f"Error terminating session: {response.status_code}")
```

---

## 🐳 Container Management

### List Available Images
```python
# Get all available container images
response = requests.get(f"{base_url}/image", headers=headers)
images = response.json()

for image in images:
    print(f"Image: {image['id']}")
    print(f"Type: {image['type']}")
    print(f"Description: {image.get('name', 'No description')}")
    print("---")
```

### Check Image Details
```python
# Get detailed information about a specific image
image_id = "images.canfar.net/skaha/astroml:latest"
response = requests.get(f"{base_url}/image", 
                       headers=headers,
                       params={"image": image_id})
                       
image_info = response.json()
print(f"Image: {image_info['id']}")
print(f"Types supported: {image_info['types']}")
```

---

## 🔄 Automation Examples

### Batch Job Launcher
```python
def launch_analysis_pipeline(data_files, analysis_script):
    """Launch multiple sessions for parallel processing"""
    
    sessions = []
    for i, data_file in enumerate(data_files):
        
        # Create session with unique name
        session_data = {
            "name": f"analysis-job-{i}",
            "image": "images.canfar.net/skaha/astroml:latest", 
            "cores": 4,
            "ram": 8,
            "kind": "headless",
            "cmd": f"python {analysis_script} {data_file}"
        }
        
        response = requests.post(f"{base_url}/session", 
                               headers=headers, 
                               data=session_data)
        
        if response.status_code == 200:
            session_id = response.json()['sessionId']
            sessions.append(session_id)
            print(f"Launched job {i}: {session_id}")
        else:
            print(f"Failed to launch job {i}: {response.text}")
    
    return sessions

# Usage
data_files = ["/arc/projects/mygroup/data/file1.fits", 
              "/arc/projects/mygroup/data/file2.fits"]
jobs = launch_analysis_pipeline(data_files, "/arc/projects/mygroup/scripts/analyze.py")
```

### Session Health Monitor
```python
def monitor_sessions(session_ids, check_interval=60):
    """Monitor multiple sessions and report status"""
    import time
    
    while session_ids:
        active_sessions = []
        
        for session_id in session_ids:
            response = requests.get(f"{base_url}/session/{session_id}", headers=headers)
            
            if response.status_code == 200:
                session = response.json()
                status = session['status']
                
                if status == 'Running':
                    active_sessions.append(session_id)
                    print(f"✓ {session_id}: Running")
                elif status == 'Terminating':
                    print(f"⏳ {session_id}: Terminating")
                elif status == 'Error':
                    print(f"❌ {session_id}: Error - {session.get('statusMessage', 'Unknown')}")
                else:
                    print(f"🏁 {session_id}: Completed")
            else:
                print(f"❓ {session_id}: Cannot check status")
        
        session_ids = active_sessions
        if session_ids:
            time.sleep(check_interval)
    
    print("All sessions completed!")

# Usage
monitor_sessions(["session1", "session2", "session3"])
```

---

## 📊 Resource Management

### Check Resource Usage
```python
# Get resource information for your sessions
response = requests.get(f"{base_url}/session", headers=headers)
sessions = response.json()

total_cores = sum(s.get('cores', 0) for s in sessions)
total_ram = sum(s.get('ram', 0) for s in sessions)

print(f"Currently using:")
print(f"  Cores: {total_cores}")
print(f"  RAM: {total_ram} GB")
print(f"  Active sessions: {len(sessions)}")
```

### Resource Limits
- **Max concurrent sessions**: 3 per user
- **Max cores per session**: Varies by project allocation
- **Max RAM per session**: Varies by project allocation
- **Session duration**: 4 days (renewable)

---

## 🐍 Python SDK

### CANFAR Python Client
Install the official Python client for easier API interaction:

```bash
pip install canfar-clients
```

```python
from canfar import skaha

# Initialize client
client = skaha.SkahaClient()

# Launch session
session = client.create_session(
    name="my-session",
    image="images.canfar.net/skaha/astroml:latest",
    session_type="notebook"
)

# Wait for session to be ready
session.wait_for_ready()
print(f"Session ready: {session.connect_url}")

# List all sessions
sessions = client.list_sessions()
for s in sessions:
    print(f"{s.name}: {s.status}")

# Cleanup
session.delete()
```

---

## 🔧 Advanced Usage

### Custom Headers and Parameters
```python
# Add custom metadata to sessions
headers_with_metadata = {
    **headers,
    "X-Session-Project": "galaxy-evolution-survey",
    "X-Session-PI": "dr.smith@university.edu"
}

# Launch with additional parameters
advanced_session = {
    "name": "advanced-analysis",
    "image": "images.canfar.net/skaha/custom-pipeline:v1.0",
    "cores": 8,
    "ram": 16,
    "kind": "notebook",
    "env": {
        "PROJECT_NAME": "GES2024",
        "DATA_PATH": "/arc/projects/ges/data"
    }
}
```

### Error Handling
```python
def robust_session_launch(session_config, max_retries=3):
    """Launch session with retry logic"""
    
    for attempt in range(max_retries):
        try:
            response = requests.post(f"{base_url}/session", 
                                   headers=headers, 
                                   data=session_config,
                                   timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 409:
                print(f"Conflict (attempt {attempt + 1}): {response.text}")
                time.sleep(5)  # Wait before retry
            else:
                print(f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Network error (attempt {attempt + 1}): {e}")
            time.sleep(5)
    
    raise Exception(f"Failed to launch session after {max_retries} attempts")
```

---

## 📚 API Documentation

### Full API Reference
- **[Skaha API Docs](https://ws-uv.canfar.net/skaha)** - Complete API specification
- **[OpenAPI Spec](https://ws-uv.canfar.net/skaha/capabilities)** - Machine-readable API definition

### Rate Limits
- **Session operations**: 10 requests per minute
- **List operations**: 30 requests per minute
- **Bulk operations**: Contact support for higher limits

---

## 🆘 Troubleshooting

### Common Issues

**Authentication Errors**
```python
# Check token validity
response = requests.get(f"{base_url}/session", headers=headers)
if response.status_code == 401:
    print("Token expired or invalid - please refresh")
elif response.status_code == 403:
    print("Insufficient permissions - check group membership")
```

**Session Launch Failures**
- **Resource limits**: Check if you're at the 3-session limit
- **Image permissions**: Ensure you have access to the container image
- **Quota exceeded**: Verify your project has available resources

**Network Issues**
- **Timeouts**: Increase request timeout for slow operations
- **Connection errors**: Check VPN if accessing from restricted networks

### Getting Help
- **API issues**: [support@canfar.net](mailto:support@canfar.net)
- **Authentication problems**: [CADC Support](mailto:support@canfar.net)
- **Community discussion**: [Discord](https://discord.gg/YOUR_INVITE_LINK)
