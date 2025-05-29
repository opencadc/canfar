# CANFAR Authorizations and Permissions

## Session Authorization

Session launching and management uses the `skaha` service. The skaha API (Application Programming Interface) definition and science platform service are available at: https://ws-uv.canfar.net/skaha

### Authentication Methods

All requests to the skaha API require CADC (Canadian Astronomy Data Centre) credentials. CANFAR provides two authentication methods:

1. **Web portal**: Handles credentials automatically using browser cookies
2. **Programmatic access**: Requires either x.509 client certificates or authorization tokens

#### Authorization Tokens

Authorization tokens provide temporary access for automated scripts and applications.

**How to obtain tokens**:
```bash
curl https://ws-cadc.canfar.net/ac/login \
  -d "username=<username>" \
  -d "password=<password>"
```

**What this does**:
- Contacts CANFAR's Access Control service over secure SSL
- Returns a time-limited access token
- Token remains valid for 48 hours

**Using tokens for API access**:
```bash
curl -H "Authorization: Bearer <token>" \
  https://ws-uv.canfar.net/skaha/v0/session
```

#### Proxy Certificates

Proxy certificates provide an alternative authentication method favored by astronomy tools.

**Installation requirement**: 
Install the [CADC Python libraries](https://github.com/opencadc/vostools/tree/master/vos) which include the `cadc-get-cert` tool.

**Generate certificate**:
```bash
cadc-get-cert -u <username>
```

**What this creates**:
- Downloads a proxy certificate to `$HOME/.ssl/cadcproxy.pem`
- Default validity: 10 days (maximum: 30 days with `--days-valid` parameter)
- Can read password from `$HOME/.netrc` file using `--netrc-file` parameter


## CANFAR `arc` File System Groups and Permissions

Groups can be assigned as either `read-only` or `read-write`.

More sophisticated management of groups, including setting default groups for a given project directory, can be done on the command line in the Science Portal, and is explained in the section below.

### Command Line Group Management

Each file or directory can have any of read (r), write (w), or execute (x) permission.  For example, a file with read-write permission is describe with rw-.

```
r = read - can see the file or directory
w = write - can modify the file or directory
x = execute - for directories, means list children.  for files, means execute file
- = does not have the given permission (r, w, or x, depending on the position of the -)
```

The following lists permission combinations for arc as seen on the command line:

```
read-only file permissions: r--
read-write file permissions: rw-
read-only directory permissions: r-x
read-write directory permissions: rwx
```

Group permissions are stored in POSIX Access Control Lists (ACLs).  To view the group permissions on a given file or directory, run the following command:

```
getfacl file-or-directory
```

There are two relevant entries in the output:

The named-group permissions, in the format `group:{group-name}:{permissions}`.  For example: `group:skaha-users:rw-`

Secondly, if a `mask` entry exists, it will change the actual (or effictive) permissions the group receives.  For example, if the following mask entry `mask::r-x` were applied to `group:skaha-users:rw-`, the effective permissions become `group:skaha-users:r--`  Effective permissions are calculated by doing an AND operation on each of the three correspsonding permissions (rwx).  The permission must exist in both the original group permissions and the mask for them to become effective.  If a mask entry does not exist, the group permissions are used directly.

To make files and directories (and their children) inherit group permissions, run *one* of the following commands:

Set the default read group:
```
setfacl -d -m group:{group-name}:r-x {read-only-dir}
```

Set the default read-write group:
```
setfacl -d -m group:{group-name}:rwx {read-write-dir}
```

The group permissions are not set on target directories themselves, only on newly created children.
To set group permissions on a single file or directory, run *one* of the following commands:

Set the read group:
```
setfacl -m group:{group-name}:r-x {read-only-dir}
```

Set the read-write group:
```
setfacl -m group:{group-name}:rwx {read-write-dir}
```

To set group permissions on an existing directory tree recursively, run *one* of the following commands:

Set the read group:
```
setfacl -R -m group:{group-name}:r-x {read-only-dir}
```

Set the read-write group:
```
setfacl -R -m group:{group-name}:rwx {read-write-dir}
```

To set group permissions on an existing directory tree recursively, and to have new children in directories of that tree inherit the group permissions, run *one* of the following commands:

Set the read group:
```
setfacl -R -d -m group:{group-name}:r-x {read-only-dir}
```

Set the read-write group:
```
setfacl -R -d -m group:{group-name}:rwx {read-write-dir}
```

![CANFAR](https://www.canfar.net/css/images/logo.png){ height="200" }
