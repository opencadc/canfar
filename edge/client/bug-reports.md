# Bug reports

[Report a problem](https://github.com/opencadc/canfar/issues/new/choose) by
describing what you were trying to do and what happened. You do not need to
know which component caused it or prepare a complete reproduction first.
For a question or general feedback, use [CANFAR Discussions](https://github.com/opencadc/canfar/discussions).

<span id="before-reporting-a-bug"></span>
<span id="how-to-report-a-bug"></span>

## Start with a short description

Give the report a descriptive title. Explain your task, what happened, and
the result you expected. If a related issue already exists, add your
experience there. You can also start a new report and let maintainers link
related work. Updating the client is not a requirement for asking for help.

In v1.5.0 and later, run:

```bash
canfar feedback
```

This prints the issue chooser URL. It does not open a browser, read your
configuration, collect diagnostics, or submit a report. If your installed
client does not have the command, use the link at the top of this page.

<span id="create-a-detailed-bug-report"></span>
<span id="what-makes-a-good-bug-report"></span>
<span id="good-bug-reports-include"></span>
<span id="avoid-these-common-issues"></span>

## Add details if you have them

Commands or steps, the client version, operating system, and a reviewed error
excerpt help maintainers investigate. Screenshots can help with browser
problems. These fields are optional. If a minimal example is difficult to
produce, describe the workflow and we can help narrow it down.

Keep one problem per report where possible. You do not need to decide
whether it belongs to the client, a storage dependency, or the service.
Maintainers handle that routing and keep you informed.

<span id="gather-system-information"></span>

## Share diagnostics selectively

`canfar version` shows the client version. A maintainer may ask for selected
details from `canfar version --debug`, which also shows Python, operating
system, dependency, and installation information. Its Python executable path
can include your username. Review it before sharing.

Do not attach credentials, full configuration files, private research data,
or unreviewed debug logs. Debug output can include response bodies and paths;
see [logging](../cli/logging.md). Email
[support@canfar.net](mailto:support@canfar.net) for account or service help
that cannot be discussed publicly.

## Security issues

Follow the [security policy](../security.md) to report vulnerabilities
privately instead of opening a public issue.

## After reporting

The team reviews feedback weekly. We may ask a focused question, link your
report to existing work, or create an implementation issue from a discussion.
Confirmed unresolved bugs are not closed just because they become quiet.

When a fix ships, we will identify the release and ask you to confirm whether
it solves the problem. We summarize feedback and progress in the existing
platform release notes every three months with each new release. See the
[community guidelines](../platform/community/guidelines.md) for roadmap
statuses and other ways to contribute.
