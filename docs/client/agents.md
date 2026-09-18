# Use CANFAR with a coding agent

Give your coding agent the CANFAR skill when you want help launching Sessions,
writing a batch workflow, inspecting a failed run, transferring research data,
or finding the right page of this documentation. The skill teaches the agent
to check your installed client, confirm your login and server, wait until a
Session is actually ready, and keep cleanup within the work you requested.

## Get the skill

```bash
npx skills add opencadc/canfar
```

The installer copies `skills/canfar` from this repository into the skills
folder of the coding agent you choose. To install by hand, copy that folder
into the location your agent documents. The skill has no scripts or
dependencies, and it is not installed by `pip install canfar`. Run the
installer again to update it.

## Ask for what you want

Invoke the skill by name, or describe CANFAR work and let the agent pick it up:

```text
/canfar start a notebook session
/canfar run reduce.py over the 400 FITS files in /arc/projects/PROJECT/raw with 40 replicas
/canfar copy results/ from my laptop to my project space
/canfar why is my session still Pending?
/canfar how do I share a directory with a collaborator?
```

The agent does better with specifics: which server and project to use, where
the input data is, where to save results, and which image or package versions
your analysis needs. For batch work, also give the script path, the inputs,
the number of replicas, and how you want failures reported. A script on your
laptop must be uploaded or included in the image before a remote Session can
run it.

## Complete login yourself

When login is needed, the agent asks you to run `canfar login cadc` or
`canfar login srcnet` in your own terminal. Enter your password or approve the
device yourself; the agent continues once your login works. Keep credentials
out of scripts, notebooks, and shared logs.

## Check the result

Expect the agent to report the Session IDs it created, the state it observed
for each, and the output paths it verified. A created Session is not
necessarily ready, and a finished Session has not necessarily produced correct
output. Keep final results under persistent storage before requesting cleanup;
the agent deletes only the Sessions it created, and only when you ask.

For details, see [Authentication and servers](../cli/authentication-contexts.md),
[Data access](data.md), [Advanced examples](advanced-examples.md), and the
[CLI reference](../cli/cli-help.md).
