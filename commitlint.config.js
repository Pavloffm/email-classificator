module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      ['fix', 'chore', 'feat', 'docs', 'refactor', 'test', 'revert', 'perf', 'ci', 'build', 'style'],
    ],
  },
};
