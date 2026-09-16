# Use CANFAR with a coding agent

Give your coding agent the CANFAR skill when you want help launching Sessions,
writing a batch workflow, inspecting a failed run, or transferring research
data. The skill explains how to check your installed client, choose a server,
use storage credentials, and keep cleanup within the work you requested.

## Get the skill

The publishable source is `skills/canfar/SKILL.md` at the root of this
repository. In a checkout of `feat/interfaces`, copy the `skills/canfar`
folder into the skills location supported by your coding agent. Follow your
agent's installation instructions; this page does not assume one agent or
installation directory. The skill has no extra scripts or dependencies.

The skill is prepared for publication with this branch. It is not installed
by `pip install canfar`. Keep its instructions aligned with your installed
client, especially while the branch's features are unreleased.

## Describe the work you want

Tell the agent which server and project to use, where the input data is, where
to save results, and which software image or package versions your analysis
needs. For example:

> Use my existing CANFAR environment. Find a notebook image for my analysis,
> confirm my project storage is accessible, and prepare a Session with the
> resources I specify. Save results under my project directory and keep the
> Session IDs so we can clean up this run when I finish.

For batch work, also give the script path, input manifest, number of replicas,
and how you want failures reported. A script on your laptop must be uploaded
or included in the image before a remote Session can run it.

## Complete login and verify the result

Complete password entry or device approval yourself when prompted. The agent
can inspect the installed command help and saved selection, but should not
copy credentials into scripts, notebooks, or shared logs.

Check that the agent reports the actual created Session IDs, their observed
state, and the verified output paths. Creating a Session does not mean it is
ready or that the analysis succeeded. Keep final results under persistent
storage before requesting cleanup.

For details, see [Authentication and servers](../cli/authentication-contexts.md),
[Data access](data.md), and the [CLI reference](../cli/cli-help.md).
