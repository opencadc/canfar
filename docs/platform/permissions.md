# CANFAR Authorisations and Permissions

## Seesion Authorisations

The session launching and management is through the `skaha` service The skaha API definition and science platform service are here:  https://ws-uv.canfar.net/skaha

### Authentication

All requests to the skaha API must be made with CADC credentials.  In the science platform the credentials are handled with cookies, but for programatic access, either x.509 client certificates or authorization tokens must be used.

#### Authorization Tokens

Tokens can be obtained from the CANFAR Access Control service by providing your CADC username and password over a secure SSL connection:

```curl https://ws-cadc.canfar.net/ac/login -d "username=<username>" -d "password=<password>"```

The token returned can then be used for making authenticated requests to skaha.  For example:

```curl -H "Authorization: Bearer <token>" https://ws-uv.canfar.net/skaha/v0/session```

Tokens are valid for 48 hours.

#### Proxy Certificates

Another way to authenticate to the skaha API is by using proxy certificates.  Using the [CADC Python libraries](https://github.com/opencadc/vostools/tree/master/vos), the `cadc-get-cert` tool will download a proxy certificate to the default location: `$HOME/.ssl/cadcproxy.pem`.

```cadc-get-cert -u <username>```

By default the proxy certificate is valid for 10 days.  This can be modified (to a maximum of 30 days) with the `--days-valid` parameter.

Instead of prompting for your password, cadc-get-cert can read it from your `$HOME/.netrc` file using the `--netrc-file` parameter.


## CANFAR `arc` File System Groups and Permissions

Groups can be assigned as either `read-only` or `read-write`.

More sophisticated management of groups, including setting default groups for a given project directory, can be done on the command line in the science portal, and is explained in the section below.

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
