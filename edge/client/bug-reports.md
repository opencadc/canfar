# Bug Reports


Thank you for taking the time to report a bug! Your feedback helps us improve CANFAR for everyone. This guide will help you create effective bug reports so we can quickly identify and resolve issues.


## Before Reporting a Bug

Before creating a new bug report, please:

- **Search existing issues**: Check if the bug has already been reported in our [GitHub Issues](https://github.com/opencadc/canfar/issues).
- **Update to the latest version**: Ensure you are using the latest version of the CANFAR Client.
- **Check the documentation**: Review our [documentation](https://opencadc.github.io/canfar/) to confirm the expected behaviour.


## How to Report a Bug

### Gather System Information

Before reporting a bug, collect detailed system information using the CANFAR CLI:

```bash
canfar version --debug
```

This command provides information about your environment:

- **Client Information**: `canfar` version, git commit info, installation method
- **Python Environment**: Python version, executable path, implementation
- **System Details**: Operating system, version, architecture, platform
- **Dependencies**: Versions of key packages that might affect functionality


### Create a Detailed Bug Report

When creating your bug report, please provide:

- **Bug Description**
    - What you were trying to do
    - What actually happened
    - What you expected to happen
- **Steps to Reproduce**: Exact steps to reproduce the behaviour, including relevant commands and options.
- **Expected Behaviour**: What you expected to happen instead.
- **System Information**: Complete output from `canfar version --debug`.
- **Error Messages and Logs**: Any error messages, stack traces, or relevant log output. Use code blocks for formatting.
- **Screenshots (if applicable)**: Screenshots that help explain the problem.
- **Additional Context**: Any other details, such as:
    - When the issue started occurring
    - Whether it happens consistently or intermittently
    - Any workarounds you have found
    - Related configuration or environment details


## What Makes a Good Bug Report


### ✅ Good Bug Reports Include

- Clear, descriptive title
- Complete system information from `canfar version --debug`
- Detailed steps to reproduce
- Expected vs. actual behaviour
- Error messages and stack traces
- Relevant context and environment details


### ❌ Avoid These Common Issues

- Vague descriptions like "it doesn't work"
- Missing system information
- Incomplete reproduction steps
- Screenshots of text instead of copy-pasted text
- Mixing multiple unrelated issues in one report


## Security Issues

If you discover a security vulnerability, please **do not** create a public issue. Instead, refer to our [Security Policy](../security.md) for instructions on how to report security issues responsibly.


## After Reporting

After you submit a bug report:

- **Monitor the issue**: Watch for responses from maintainers
- **Provide additional information**: Be ready to answer follow-up questions
- **Test fixes**: Help test proposed solutions when available
- **Update the issue**: Let us know if the problem is resolved

Thank you for helping make Canfar better! 🚀