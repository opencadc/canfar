# Get help and shape CANFAR

[CANFAR Discussions](https://github.com/opencadc/canfar/discussions) is the
public home for questions, feedback, ideas, and research workflows. You do
not need to contribute code or know which component caused a problem.

## Choose where to post

| You want to | Where to start |
| --- | --- |
| Ask how to do something or get unstuck | [Q&A](https://github.com/opencadc/canfar/discussions/categories/q-a) |
| Describe what worked, was confusing, or needs a workaround | [Feedback](https://github.com/opencadc/canfar/discussions/categories/feedback) |
| Propose an improvement or add your use case to one | [Ideas](https://github.com/opencadc/canfar/discussions/categories/ideas) |
| Follow releases and the pinned roadmap | [Announcements](https://github.com/opencadc/canfar/discussions/categories/announcements) |
| Share a notebook, workflow, or practical tip | [Show and tell](https://github.com/opencadc/canfar/discussions/categories/show-and-tell) |
| Report a failure or correct the documentation | [Issue forms](https://github.com/opencadc/canfar/issues/new/choose) |

Start in Feedback if you are unsure. A short description is enough. Tell us
what you were trying to do and what happened. Commands, examples, and
screenshots are optional. We can help gather details or move a conversation.
Try to keep one concern in each topic so others can follow it.

You need a GitHub account to post or vote. You can instead email
[support@canfar.net](mailto:support@canfar.net) or use
[CANFAR Discord](https://discord.gg/vcCQ8QBvBa). Maintainers ask before
publishing a summary of private feedback and relay updates through your
original channel. You do not need to repeat a report in several places.

## Give feedback on the Data beta

The `canfar data` commands and the Python storage tools in `canfar.storage`
have been available in beta since client v1.5.0. Use the
[installation guide](../../client/get-started.md#install) to update your client.

Tell us what you tried, where you needed a workaround, and what would make
the task easier. Successful workflows are useful too. Start a Feedback
discussion, or join an existing conversation about the same workflow.
Maintainers will link any issue or proposal that grows out of your report.

In v1.5.0 and later, this command prints the feedback URL:

```bash
canfar feedback
```

It does not open a browser, collect diagnostics, or submit anything. It works
without authentication or a working configuration. On an older client, use
the links on this page. Data help identifies the beta; ordinary Data
operations and Python calls print no beta notice.

## Follow an idea through the roadmap

Open the pinned roadmap in Announcements, then follow an individual proposal
to add your use case or upvote it. GitHub supports upvotes and removing an
upvote. Explain concerns in a comment rather than treating reactions as a
downvote score.

| Status | Meaning |
| --- | --- |
| Considering | A proposal without an implementation commitment |
| Planned | The team has accepted the scope and intends to implement it |
| In progress | Implementation has started; a merged change may still await release |
| Released | The change is available in a published release or deployed documentation |
| Not planned | The team is not pursuing it; the discussion explains why |

Votes inform decisions alongside scientific impact, data safety,
accessibility, feasibility, and maintenance cost. They do not guarantee
delivery. Dates appear only when the team has made a delivery commitment.
The proposal's status label is authoritative; the pinned roadmap links the
proposals and their implementation records.

## What happens after you post

The team reviews new contributions each week. A maintainer will answer,
ask a focused question, link existing work, or identify the next action.
Reports about dependencies remain welcome here; maintainers handle upstream
coordination. There is no guaranteed response deadline.

We summarize community feedback in the platform release notes every three
months with the new release. Each summary links reports to released changes,
work in progress, decisions, and outstanding questions. We also update
individual conversations when something changes, so you need not wait for
the next release to hear about a decision.

When an answer solves your question, mark it as accepted. A workaround can
answer a question while a linked bug remains open. When a fix ships, the team
will identify the release and ask whether it resolves your problem.
Confirmed unresolved bugs stay open unless the team explicitly decides not
to pursue them. We do not automatically close reports because they are quiet.

## Participate and help others

You can contribute by answering a question, trying a reproduction, improving
an example, testing a fix, or sharing a workflow. Maintainers use
`help wanted` and `good first issue` when a task has a defined scope and a
reviewer. Read the [contributor guide](../../contributing.md) for code changes.

Criticism and disagreement are welcome. Discuss the behavior or proposal
without attacking the person. Incomplete reports and imperfect English are
not misconduct. The [Code of Conduct](../../conduct.md) applies across our
community spaces and explains private reporting and enforcement.

## Keep private information private

Do not post passwords, tokens, certificates, full configuration files, or
private research data. Review error excerpts and screenshots before sharing.
Debug logs can contain response bodies and paths.

Use [support@canfar.net](mailto:support@canfar.net) for account access,
service incidents, and private data concerns. Follow the
[security policy](../../security.md) for vulnerabilities. Community
Discussions are not an emergency service channel.
