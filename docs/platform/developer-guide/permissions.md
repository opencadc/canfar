# CANFAR Authorization and Permissions Guide

Comprehensive guide to authentication, session management, and file permissions on the CANFAR Science Platform.

## 🔐 Session Authentication

### Overview

The **skaha service** manages session launching and access control. All interactions require proper CADC (Canadian Astronomy Data Centre) credentials.

**API Endpoint**: [https://ws-uv.canfar.net/skaha](https://ws-uv.canfar.net/skaha)

**What this means**: You need valid CADC credentials to launch containers, access files, or use the Science Platform programmatically.

## 🎫 Authentication Methods

### Method 1: Authorization Tokens (Recommended)

**Best for**: Programmatic access, API calls, temporary authentication

#### Obtaining Tokens

```bash
# Get a 48-hour token
curl https://ws-cadc.canfar.net/ac/login \
  -d "username=your_username" \
  -d "password=your_password"
```

**What this does**: Exchanges your CADC username/password for a temporary token valid for 48 hours.

#### Using Tokens

```bash
# Example: List your active sessions
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://ws-uv.canfar.net/skaha/v0/session

# Example: Launch a new session
curl -H "Authorization: Bearer YOUR_TOKEN" \
  -d "name=my-session" \
  -d "image=images.canfar.net/skaha/astroml:latest" \
  https://ws-uv.canfar.net/skaha/v0/session
```

### Method 2: Proxy Certificates

**Best for**: Long-term automation, file transfers, command-line tools

#### Obtaining Certificates
From the `cadcutils` python package (installable with `pip`)
```bash
# Get a 10-day certificate (default)
cadc-get-cert -u your_username

# Extended certificate (up to 30 days)
cadc-get-cert -u your_username --days-valid 30

# Use credentials from .netrc file
cadc-get-cert -u your_username --netrc-file
```

**What this does**: Downloads a proxy certificate to `$HOME/.ssl/cadcproxy.pem` that authenticates you for the specified period.

#### Using Certificates

```bash
# Example: API call with certificate
curl -E ~/.ssl/cadcproxy.pem \
  https://ws-uv.canfar.net/skaha/v0/session

# Example: Download files with authentication
wget --certificate ~/.ssl/cadcproxy.pem \
  --ca-certificate ~/.ssl/cadcproxy.pem \
  https://your-authenticated-download-url
```

### Method Comparison

| Method | Duration | Best For | Setup Required |
|--------|----------|----------|----------------|
| **Tokens** | 48 hours | API calls, temporary scripts | Username/password |
| **Certificates** | 10-30 days | File transfers, automation | Install cadcutils |

---

## 📁 ARC File System Permissions

### Understanding Permission Basics

CANFAR uses **POSIX permissions** combined with **Access Control Lists (ACLs)** for fine-grained access control.

#### Permission Types

| Symbol | Permission | For Files | For Directories |
|--------|------------|-----------|-----------------|
| **r** | Read | View file content | List directory contents |
| **w** | Write | Modify file | Create/delete files inside |
| **x** | Execute | Run as program | Enter directory |
| **-** | No permission | Cannot access | Cannot access |

#### Common Permission Patterns

```bash
# File permissions
r--  # Read-only file
rw-  # Read-write file

# Directory permissions  
r-x  # Read-only directory (can list and enter)
rwx  # Read-write directory (full access)
```

**Why directories need 'x'**: The execute permission on directories allows you to "enter" them and access files inside.

### Viewing Current Permissions

#### Check Basic Permissions

```bash
# View permissions for files and directories
ls -la /arc/projects/yourproject/

# Example output:
# drwxrwx---  2 user projectgroup  4096 Nov 15 10:30 data/
# -rw-rw-r--  1 user projectgroup  1024 Nov 15 10:15 analysis.py
```

#### Check Advanced Permissions (ACLs)

```bash
# View detailed access control lists
getfacl /arc/projects/yourproject/data/

# Example output:
# # file: data/
# # owner: username
# # group: projectgroup
# user::rwx
# group::rwx
# group:external-collaborators:r-x
# mask::rwx
# other::---
```

**What this shows**:
- **Basic permissions**: User/group/other access
- **Named groups**: Additional groups with specific permissions
- **Mask**: Limits maximum permissions for groups
- **Effective permissions**: Actual permissions after mask is applied

### Managing Group Permissions

#### Understanding Group Access

Groups allow multiple users to share access to project directories:

- **Project groups**: Automatically created for project members
- **Named groups**: Custom groups for specific collaborations
- **Effective permissions**: Calculated from group permissions AND mask

#### Setting Group Permissions

**🎯 Single File or Directory**:

```bash
# Grant read-only access to a group
setfacl -m group:external-group:r-x /arc/projects/yourproject/public_data/

# Grant read-write access to a group
setfacl -m group:collaborators:rwx /arc/projects/yourproject/shared/
```

**🎯 Entire Directory Tree (Recursive)**:

```bash
# Apply read-only permissions to existing files
setfacl -R -m group:external-group:r-x /arc/projects/yourproject/public_data/

# Apply read-write permissions to existing files  
setfacl -R -m group:collaborators:rwx /arc/projects/yourproject/shared/
```

**🎯 Default Permissions for New Files**:

```bash
# New files will inherit read-only group permissions
setfacl -d -m group:external-group:r-x /arc/projects/yourproject/public_data/

# New files will inherit read-write group permissions
setfacl -d -m group:collaborators:rwx /arc/projects/yourproject/shared/
```

**🎯 Complete Setup (Existing + Future Files)**:

```bash
# Set permissions on existing files AND make new files inherit permissions
setfacl -R -d -m group:collaborators:rwx /arc/projects/yourproject/shared/
```

**What each option does**:
- **`-m`**: Modify permissions
- **`-R`**: Apply recursively to all existing files/subdirectories
- **`-d`**: Set default permissions for newly created files
- **`-d -R`**: Both recursive on existing files AND defaults for new files

### Understanding Permission Masks

#### What are Masks?

**Masks** limit the maximum permissions that can be granted to groups, providing an additional security layer.

```bash
# Example: Group has rwx, but mask limits to r-x
group:collaborators:rwx    # Requested permissions
mask::r-x                 # Mask limitation
# Effective result: r-x   # Actual permissions granted
```

#### Working with Masks

```bash
# View current mask
getfacl /arc/projects/yourproject/data/ | grep mask

# Set a restrictive mask (limits write access)
setfacl -m mask::r-x /arc/projects/yourproject/public/

# Set a permissive mask (allows full group permissions)
setfacl -m mask::rwx /arc/projects/yourproject/private/
```

## 💡 Best Practices

### Project Organization

```bash
# Recommended project structure with permissions
/arc/projects/yourproject/
├── public/          # setfacl -d -m group:everyone:r-x
├── shared/          # setfacl -d -m group:collaborators:rwx  
├── private/         # setfacl -d -m group:core-team:rwx
└── scratch/         # setfacl -d -m group:project-members:rwx
```

### Permission Management Workflow

1. **Plan your collaboration model**:
   - Who needs read access?
   - Who needs write access?
   - What data should be public vs. private?

2. **Set up directory structure first**:
   ```bash
   mkdir -p /arc/projects/yourproject/{public,shared,private,data,results}
   ```

3. **Apply default permissions**:
   ```bash
   # Public data - read-only for external users
   setfacl -d -m group:external-users:r-x /arc/projects/yourproject/public/
   
   # Shared workspace - read-write for collaborators
   setfacl -d -m group:collaborators:rwx /arc/projects/yourproject/shared/
   
   # Private data - project team only
   setfacl -d -m group:core-team:rwx /arc/projects/yourproject/private/
   ```

4. **Test permissions**:
   ```bash
   # Verify setup works as expected
   getfacl /arc/projects/yourproject/shared/
   
   # Test as different users if possible
   ```

### Security Considerations

- **Principle of least privilege**: Grant minimum permissions necessary
- **Regular audits**: Periodically review group memberships and permissions
- **Sensitive data**: Use private directories with restricted group access
- **Temporary access**: Use tokens for short-term programmatic access

## 🚨 Troubleshooting

### Permission Denied Errors

```bash
# Check your current groups
groups

# Check directory permissions
ls -la /arc/projects/yourproject/
getfacl /arc/projects/yourproject/problematic_directory/

# Verify you're in the required group
# Contact your project administrator if needed
```

### Authentication Issues

```bash
# Check token validity
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://ws-cadc.canfar.net/ac/whoami

# Check certificate validity
cadc-info -u your_username

# Refresh certificate if expired
cadc-get-cert -u your_username
```

### Group Membership Problems

```bash
# Check which groups you belong to
groups

# Check which groups can access a directory
getfacl /arc/projects/yourproject/directory_name/

# Contact project administrators to modify group membership
```

## 🆘 Getting Help

- **Permission issues**: Contact your project administrator
- **Group membership**: Email [support@canfar.net](mailto:support@canfar.net)
- **Authentication problems**: Check [CADC documentation](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/doc/)
- **API documentation**: See [skaha API docs](https://ws-uv.canfar.net/skaha)

## 🔗 Related Documentation

- **[API access guide](api.md)** - Programmatic platform usage
- **[Storage guide](../user-guide/storage/index.md)** - Understanding CANFAR file systems
- **[Storage guide](../user-guide/storage/index.md)** - Complete data management with proper authentication
