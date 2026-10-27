# Community triage and release updates

The [community guidelines](../platform/community/guidelines.md) describe the
public workflow. This page is the maintainer procedure. Keep substantive
decisions in the original public conversation or its linked implementation
record, rather than creating another specification here.

## Responsibilities and cadence

`@shinybrar` remains accountable for repository intake. Record the weekly duty
maintainer and an available backup in the team's existing handoff. The
repository owner covers intake when nobody else is assigned. The duty
maintainer organizes reports; the responsible maintainer decides scope and
delivery. Ask before assigning implementation work to another contributor.

Review intake weekly. Summarize community progress every three months in the
existing platform release notes, alongside the new release. Publish a short
Discussion announcement linking those notes. Do not create a separate
monthly digest or another release history. Update individual conversations
when decisions or release availability change.

Retain support@canfar.net for service help and the private conduct contact in
[the Code of Conduct](../conduct.md). An uninvolved maintainer reviews a
dispute involving the moderator. Do not invent a new support mailbox or
publish a response-time promise without staffing it.

## Discussion layout

| Section | Categories |
| --- | --- |
| Get help and shape CANFAR | Q&A, Feedback, Ideas |
| News and community | Announcements, Show and tell, Polls |

Rename General to Feedback. Q&A uses the answerable format; Announcements
uses the maintainer announcement format. Feedback, Ideas, and Show and tell
are open discussions. Keep Polls for occasional focused questions.

Check live state before posting or pinning a welcome discussion, roadmap, or
Data beta invitation to avoid duplicates. The v1.5.0 client is published.
The former `.github/discussions/` drafts are no longer in this checkout;
the dated record below describes the October 16 setup.

## Labels

Reuse `bug`, `documentation`, `enhancement`, `question`, `duplicate`,
`help wanted`, and `good first issue`. Add `area:data` to Data-related
conversations and `beta` when the report concerns a beta feature. Preserve
unrelated labels. Only use contribution labels when scope, acceptance
criteria, and a reviewer are available.

Follow [the existing triage roles](triage-labels.md). An acknowledgement alone
does not complete triage. `needs-triage` means classification or a next action
is still owed. Replace it with `needs-info` only after asking a concrete
question. When the answer arrives, restore `needs-triage`. Keep at most one
canonical triage-role label at a time.

Use exactly one of these labels on each roadmap proposal discussion:

| Label | Meaning |
| --- | --- |
| `roadmap:considering` | Proposal without an implementation commitment |
| `roadmap:planned` | Accepted scope with intent to implement |
| `roadmap:in-progress` | Implementation underway or merged but awaiting release |
| `roadmap:released` | Available to users in a release or deployed documentation |
| `roadmap:not-planned` | Declined or deferred indefinitely, with an explanation |

The discussion label is authoritative. Update the pinned index and leave a
status comment when changing it. Keep delivery details in the linked issue
and PR. Do not duplicate roadmap labels across every implementation record.
Do not describe a merged change as released until users can access it.

## Weekly review

Use GitHub's native searches:

```text
repo:opencadc/canfar is:issue is:open label:needs-triage
repo:opencadc/canfar is:discussion is:open label:needs-triage
repo:opencadc/canfar is:discussion is:open category:"Q&A" is:unanswered
repo:opencadc/canfar is:open label:needs-info
```

Check reported content as well as these queues. Identify service incidents,
possible data loss, and security concerns first and use the established
support route when they become known. Then review new reports, unanswered
questions, work waiting on maintainers or upstream projects, and proposals
needing a decision. Record the next responder and next action before handing
over. A confirmed unresolved defect does not expire because it is quiet.

| Situation | Action |
| --- | --- |
| Usage question | Answer and link documentation. Mark an answer only when it addresses the question; silence is not confirmation |
| Feedback reveals a bug | Create a linked issue, summarize relevant replies, and preserve the discussion |
| Idea accepted | Explain the reason, scope the implementation issue, and set the proposal to Planned |
| Duplicate | Copy useful new evidence to the canonical record, link it, and explain closure |
| Upstream defect | File or link the upstream issue and remain the CANFAR contact |
| Missing information | Ask for the smallest useful detail; remind once after two weekly reviews. After four weeks, review manually and close only when progress is impossible, with reopening instructions |
| Fix merged | Link the change and say whether a published release is still pending |
| Fix released | Reply to the original report with the version and docs, and ask the reporter to confirm |
| Private feedback | Ask before publishing a reviewed summary; relay updates through the original channel |

Creating an issue from a discussion preserves the discussion and copies its
opening post and labels. Add relevant evidence from replies and remove
discussion-only roadmap labels from the new issue. For a question filed as
an issue, answer or convert it to Q&A and explain where the conversation
continues. Users should not have to rewrite their first contribution.

## Saved replies

Adapt these replies to the actual report. Always name the next action or
link the relevant record.

**Clarification**

> Thanks for describing the transfer. Can you share the command with private
> path components replaced, and the final error line? That should help us
> distinguish a path problem from a transfer failure. You do not need to send
> the files or your full logs.

**Duplicate**

> This appears to be the same problem tracked in the linked issue. Your
> report adds a useful detail, which I have included there. We will post
> progress in that issue. You do not need to submit another report.

**Merged but unreleased**

> The fix has merged, but it is not in a published client release yet. We
> will update this thread when you can install it. The workaround above
> still applies in the meantime.

For a declined proposal, explain the concrete reason, any available
alternative, and what new evidence could change the decision. Do not use a
generic closure message. A report closed for missing information should say
what information would let the team reopen it.

## Conduct moderation

Ordinary criticism, frustration, disagreement, and incomplete reports remain
welcome. Follow the existing Code of Conduct for correction, warning, and
bans. Do not use conduct enforcement to settle a product-priority dispute.

Contain harassment, spam, or exposed sensitive information when encountered.
Use GitHub's hide, edit-history removal, lock, and report controls as
appropriate. Escalate organization-level actions to an authorized owner.
Explain moderation decisions where appropriate, while keeping incident
details in the team's existing private process. Closing a resolved or
duplicate conversation does not require locking it.

## Augment each quarterly release

Add a community-feedback section to the existing release notes. Include
only verified changes and decisions:

- released changes, with links to the original reports and release details;
- work underway and its next action;
- accepted, deferred, or declined proposals and the reasons;
- unresolved problems and the information needed; and
- one focused question about a real research workflow.

Omit empty sections. Credit contributions with the contributor's agreement.
The Discussion announcement links this section instead of copying the full
notes. Review the pinned roadmap at the same time and when status changes.

Review unanswered questions, time to first human response, work waiting on
maintainers, and reports that led to fixes or documentation changes. Exclude
bot acknowledgements and do not treat raw votes or closure counts as success.

## Launch checks

Create labels before enabling forms that refer to them. Discussion form
filenames must match category slugs; forms activate on the default branch.
Check the chooser as an ordinary contributor, since maintainers can see
options other users cannot. Verify all destinations after setup.

Before announcing a client release, verify its GitHub and PyPI publication
and check the installed help for each documented command. Update upcoming
wording in current docs to released wording. Retain the Data beta designation
without applying it to unrelated client features.

## Publication record

Community setup on October 16, 2026:

| Historical post source | Destination or condition recorded on October 16 |
| --- | --- |
| `.github/discussions/welcome.md` | [Welcome, discussion 6](https://github.com/opencadc/canfar/discussions/6), updated in place |
| `.github/discussions/roadmap.md` | [Roadmap, discussion 345](https://github.com/opencadc/canfar/discussions/345) |
| `.github/discussions/idea-create-timeouts.md` | [Slow responses, discussion 343](https://github.com/opencadc/canfar/discussions/343), linked to issue 51 |
| `.github/discussions/idea-session-counts.md` | [Session counts, discussion 344](https://github.com/opencadc/canfar/discussions/344), linked to issue 140 |
| `.github/discussions/data-beta.md` | Draft until v1.5.0 is published; then post in Feedback and pin |
| `.github/discussions/release-announcement.md` | Draft until v1.5.0 and the augmented 2026.3 notes are published; post in Announcements |
| `.github/discussions/show-and-tell.md` | Draft until v1.5.0 and its Data guides are published; post in Show and tell |

This table records the setup at that date, not current publication status.
The local draft files have since been removed. Read the live discussions
before updating or publishing a post. Forms and chooser changes activate
when the repository changes reach the default branch.
