# Using VOS Tools

Examples for using VOSpace command-line tools (vcp, vls, vrm) and notes on authentication and certificates.

VOS Tools provide command-line access to CANFAR VOSpace and the Science Portal storage.

Install instructions and details are available on CANFAR's storage documentation (see CANFAR storage docs).

Typical commands:

```sh
vcp localfile arc:home/[username]
vcp vos:[username]/remotefile ./
vls vos:[username]
vrm vos:[username]/file
```

If you see an expired certificate error, update it with:

```sh
cadc-get-cert -u [username]
```

The most efficient way to transfer files in and out of CANFAR's Science
Portal is to use the VOS Tools, which are also used for interacting with CANFAR's VOSpace.

Instructions for installing VOS Tools on your personal computer are
located in CANFAR's storage documentation under the section "The vos Python module and command line client".

Instructions on how to use this tool, including some basic examples, are
found on the same webpage. In brief, this tool runs on the command line
with syntax similar to the linux `scp` command. File locations within
CANFAR systems are specified with *vos* for VOSpace and *arc* for the
Science Portal. For example, to copy a file from your personal computer
to your home directory in the Science Portal, you would type the
following on your local computer:

```sh
vcp myfile.txt arc:home/[username]
```

To copy a file from VOSpace to your personal computer, you would use:

```sh
vcp vos:[username]/myfile.txt ./
```

To copy files from the Science Portal to VOSpace, you would similarly
use the command:

```sh
vcp myfile.txt vos:[username]
```

Note that VOS Tools use a security certificate which needs to be updated periodically. If you get an error message stating:

```sh
ERROR:: Expired cert.
```

Update by running:

```sh
cadc-get-cert -u [username]
```

and enter your password for CADC/CANFAR services at the prompt.
