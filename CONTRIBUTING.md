# 如何贡献 | How to contribute

我们非常欢迎您对KBS_Agent_A2A项目的贡献和补丁。

We'd love to accept your patches and contributions to the KBS_Agent_A2A project.

## 贡献流程 | Contribution process

### 基本步骤 | Basic steps

1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m '添加一些功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个Pull Request

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### 代码审查 | Code reviews

所有提交，包括项目成员的提交，都需要审核。我们使用GitHub pull requests进行审核。请参考[GitHub帮助](https://help.github.com/articles/about-pull-requests/)了解更多关于使用pull requests的信息。

All submissions, including submissions by project members, require review. We use GitHub pull requests for this purpose. Consult [GitHub Help](https://help.github.com/articles/about-pull-requests/) for more information on using pull requests.

### 编码风格 | Coding style

为了保持代码库的一致性和可读性，请遵循以下编码风格指南：

- 使用4个空格进行缩进（不使用制表符）
- 每行代码不超过100个字符
- 遵循PEP 8 Python编码风格指南
- 为所有函数和类编写文档字符串
- 对公共API进行单元测试

To maintain consistency and readability in the codebase, please follow these coding style guidelines:

- Use 4 spaces for indentation (no tabs)
- Keep lines under 100 characters
- Follow PEP 8 Python coding style guide
- Write docstrings for all functions and classes
- Unit test all public APIs

### 提交信息 | Commit messages

请使用清晰、描述性的提交信息，格式如下：

```
简短（50个字符或更少）的总结

更详细的解释文本，如有必要。将其控制在每行约72个字符。
在某些情况下，第一行被视为提交消息的主题，其余文本为正文。
分隔主题和正文的空行至关重要（除非你完全省略了正文）；
git log、git rebase等工具可能会在你省略它时产生混淆。

解释本次提交解决的问题。关注更改的原因，而不是方式
（代码会展示这一点）。是否有副作用或其他不直观的结果？
在这里解释它们。
```

Please use clear, descriptive commit messages with the following format:

```
Short (50 chars or less) summary

More detailed explanatory text, if necessary. Wrap it to about 72
characters. In some contexts, the first line is treated as the
subject of the commit and the rest of the text as the body. The
blank line separating the summary from the body is critical (unless
you omit the body entirely); tools like git log, git rebase can
get confused if you run the two together.

Explain the problem that this commit is solving. Focus on why you
are making this change as opposed to how (the code explains that).
Are there side effects or other unintuitive consequences of this
change? Here's the place to explain them.
```

### 测试 | Testing

确保所有新代码都包含适当的测试：

- 单元测试应放在 `tests/` 目录中
- 使用 `pytest` 运行测试
- 确保所有测试都通过，并且代码覆盖率保持在80%以上

Make sure all new code includes appropriate tests:

- Unit tests should be placed in the `tests/` directory
- Use `pytest` to run tests
- Ensure all tests pass and code coverage remains above 80%

## 许可证 | License

通过贡献KBS_Agent_A2A项目，您同意您的贡献将根据项目的[Apache 2.0许可证](LICENSE)进行许可。

By contributing to KBS_Agent_A2A, you agree that your contributions will be licensed under the project's [Apache 2.0 License](LICENSE).