# CANFAR Agent Skill

Use your coding agent to launch a notebook, plan a batch workflow, move research
data, or find answers in the CANFAR documentation. The official `canfar` skill
provides instructions for these tasks and is maintained in the
[CANFAR repository](https://github.com/opencadc/canfar/tree/main/skills/canfar).

## Install the skill

You need a local coding agent, [Node.js with npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm/),
and [Git](https://git-scm.com/downloads). The `skills` installer requires
Node.js 22.20.0 or newer as of September 2026; see its
[current requirements](https://github.com/vercel-labs/skills/blob/main/package.json).

In your project's terminal, run:

```bash
npx skills add opencadc/canfar --skill canfar
```

This uses the [skills.sh installer](https://www.skills.sh/docs/cli) to install
the `canfar` skill from the official repository. If npm asks to download the
`skills` package, confirm to continue. Select your coding agent and choose
the installation scope:

| Scope | When to choose it |
| --- | --- |
| Project | You want the skill available in the project where you ran the command. |
| Global | You want it available to your selected agent across your projects on this machine. |

To select Global directly, add `--global`:

```bash
npx skills add opencadc/canfar --skill canfar --global
```

If the installer asks for an installation method, keep its recommended
symlink option, or choose Copy when your environment does not support
symlinks. The [installer reference](https://github.com/vercel-labs/skills#installation-methods)
explains both methods.

The skill installs instructions for your agent. To operate CANFAR, you also
need the [CANFAR client](../client/get-started.md) and an
[account with access](get-started.md). You can ask documentation questions
before setting those up.

## Use the skill in your agent

Choose the tab for your local agent. Each tab gives an optional command to
select that agent during installation, followed by a prompt to enter in its
chat. You only need to install once for your chosen scope.

=== "OpenAI Codex"

    In the Codex command-line interface (CLI) or editor extension, type `$`
    and select `canfar`, or find it through `/skills`. Then send:

    ```text
    $canfar explain where I should save my CANFAR results so they survive the end of a session.
    ```

    See [Codex skill invocation](https://learn.chatgpt.com/docs/build-skills#how-chatgpt-and-codex-use-skills).

=== "Claude Code"

    In Claude Code, invoke the skill by name:

    ```text
    /canfar explain where I should save my CANFAR results so they survive the end of a session.
    ```

    See [Claude Code skills](https://code.claude.com/docs/en/skills).

=== "GitHub Copilot in VS Code"

    In VS Code chat, type `/`, select `canfar`, and add your request:

    ```text
    /canfar explain where I should save my CANFAR results so they survive the end of a session.
    ```

    See [VS Code skill commands](https://code.visualstudio.com/docs/agent-customization/agent-skills#use-skills-as-slash-commands).

=== "Cursor"

    In Cursor Agent chat, type `/`, select `canfar`, and add your request:

    ```text
    /canfar explain where I should save my CANFAR results so they survive the end of a session.
    ```

    See [Cursor skills](https://cursor.com/docs/skills#how-skills-work).

These agents can also select the skill when a request matches its description.
Invoking it explicitly is a useful first check that the agent can find it.

## Ask for what you want

After selecting the skill, describe the task and the result you expect.
Replace `SERVER`, `PROJECT`, and `SESSION_ID` with your own values.

### Start a notebook

```text
Start a CANFAR notebook on cadc for my work.
Use an available astronomy image, wait until the Session is Running,
and give me its connection link and ID.
```

### Plan a batch run

```text
Plan a CANFAR batch run for reduce.py over the FITS files
in /arc/projects/{PROJECT}/raw. Use four replicas and save outputs
in /arc/projects/{PROJECT}/reduced. Check how the script will reach
the remote Sessions and show me the plan before submitting it.
```

### Copy results

```text
Copy ./results from my laptop to arc:/projects/PROJECT/results
and check that the expected files arrived.
```

### Diagnose a Session

```text
Find out why CANFAR Session SESSION_ID is still Pending
and explain what I should do next.
```

Include the Science Platform Server, project, input and output paths, and any
Container Image or package versions your analysis requires. Say when you want
a plan before execution. Your agent uses the tools and permissions available
in the environment where it runs.

## Complete login yourself

The skill tells the agent to check your installed client and use its command
help. When you need to authenticate, it asks you to log in through your
Identity Provider: the Canadian Astronomy Data Centre (CADC) or the SKA
Regional Centre Network (SRCNet). Run the appropriate command in your own
terminal:

=== "CADC"

    ```bash
    canfar login cadc
    ```

=== "SRCNet"

    ```bash
    canfar login srcnet
    ```

Enter your password or approve the device yourself, then tell the agent to
continue. Keep credentials out of chat, scripts, and shared logs. See
[Authentication and servers](../cli/authentication-contexts.md) for setup and
re-login guidance.

## Check the result

The skill asks the agent to report the Session IDs, observed states, and
verified output paths. A created Session has been accepted; it still needs
to become Running. For a task that produces data, successful completion also
requires checking its output on persistent storage.

Review those results before requesting cleanup. The skill instructs the agent
to keep cleanup within the work you authorized.

## Update or remove the skill

List installed skills to check that `canfar` is present:

```bash
npx skills list
```

Choose the scope you used when installing to update only CANFAR:

=== "Project"

    Run from the same project directory:

    ```bash
    npx skills update canfar --project
    ```

=== "Global"

    ```bash
    npx skills update canfar --global
    ```

To uninstall it, use `npx skills remove canfar` from the project directory,
or `npx skills remove canfar --global` for a global installation.
These commands follow the [skills CLI reference](https://github.com/vercel-labs/skills#other-commands).

## If the skill does not appear

1. Run `npx skills list` and check the reported agent and installation scope.
2. For a Project installation, open that project in your agent. Confirm that
   installation ran on the same machine as the agent.
3. Use the skill picker described in your agent's tab. If Codex has not picked
   up a change, restart it. Restart Cursor to trigger discovery at startup.
4. If the installer rejects a command or reports an unsupported Node.js
   version, check the [current installer requirements and options](https://github.com/vercel-labs/skills).

For CANFAR workflow help, continue with [Getting started](get-started.md),
[Data access](../client/data.md), or [Support](support/index.md).
