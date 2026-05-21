# Issue Tracker: GitHub

Issues and PRDs for this repo live in GitHub Issues for `opencadc/canfar`.

Use the `gh` CLI from the repository checkout so the repository is inferred from `git remote -v`.

## Conventions

- Create issue: `gh issue create --title "..." --body "..."`
- Read issue: `gh issue view <number> --comments`
- List issues: `gh issue list --state open --json number,title,body,labels,comments`
- Comment: `gh issue comment <number> --body "..."`
- Add label: `gh issue edit <number> --add-label "..."`
- Remove label: `gh issue edit <number> --remove-label "..."`
- Close issue: `gh issue close <number> --comment "..."`

## Skill Rules

When a skill says "publish to the issue tracker", create a GitHub issue.

When a skill says "fetch the relevant ticket", run `gh issue view <number> --comments`.

Do not use Jira, local markdown, or another tracker for repo work unless the user explicitly overrides this file.
