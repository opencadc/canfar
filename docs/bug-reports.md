# Bug Reports

Thank you for taking the time to report a bug! Your feedback helps us improve Canfar for everyone. This guide will help you create effective bug reports that enable us to quickly identify and fix issues.

## Before Reporting a Bug

Before creating a new bug report, please:

1. **Search existing issues**: Check if the bug has already been reported in our [GitHub Issues](https://github.com/opencadc/canfar/issues)
2. **Update to the latest version**: Ensure you're using the latest version of Canfar Client
3. **Check the documentation**: Review our [documentation](https://opencadc.github.io/canfar/) to confirm the expected behavior

## How to Report a Bug

### Gather System Information

Before reporting a bug, collect detailed system information using the Canfar CLI:

```bash
canfar version --debug
```

This command provides comprehensive information about your environment, including:

- **Client Information**: Canfar version, git commit info, and installation method
- **Python Environment**: Python version, executable path, and implementation
- **System Details**: Operating system, version, architecture, and platform
- **Dependencies**: Versions of key packages that might affect functionality

### Create a Detailed Bug Report

When creating your bug report, include the following sections:

1. **Bug Description**: 
    Provide a clear and concise description of what the bug is,
    - What you were trying to do
    - What actually happened
    - What you expected to happen
2. **Steps to Reproduce**: List the exact steps to reproduce the behavior, including any relevant commands and options.
3. **Expected Behavior**: Describe what you expected to happen instead
4. **System Information**: Include the complete output from `canfar version --debug`
5. **Error Messages and Logs**: Include any error messages, stack traces, or relevant log output. Use code blocks to format them properly.
6. **Screenshots (if applicable)**: Include screenshots that might help explain the problem
7. **Additional Context**: Add any other context about the problem, such as
    - When the issue started occurring
    - Whether it happens consistently or intermittently
    - Any workarounds you've found
    - Related configuration or environment details

## What Makes a Good Bug Report

### ✅ Good Bug Reports Include:
- Clear, descriptive title
- Complete system information from `canfar version --debug`
- Detailed steps to reproduce
- Expected vs. actual behavior
- Error messages and stack traces
- Relevant context and environment details

### ❌ Avoid These Common Issues:
- Vague descriptions like "it doesn't work"
- Missing system information
- Incomplete reproduction steps
- Screenshots of text instead of copy-pasted text
- Mixing multiple unrelated issues in one report

## Security Issues

If you discover a security vulnerability, please **do not** create a public issue. Instead, please refer to our [Security Policy](security.md) for instructions on how to report security issues responsibly.

## Getting Help

If you're not sure whether something is a bug or need help with usage:

- Check our [documentation](https://opencadc.github.io/canfar/)
- Ask questions in [GitHub Discussions](https://github.com/opencadc/canfar/discussions)
- Review existing [GitHub Issues](https://github.com/opencadc/canfar/issues)

## After Reporting

After you submit a bug report:

1. **Monitor the issue**: Watch for responses from maintainers
2. **Provide additional information**: Be ready to answer follow-up questions
3. **Test fixes**: Help test proposed solutions when available
4. **Update the issue**: Let us know if the problem is resolved

Thank you for helping make Canfar better! 🚀
