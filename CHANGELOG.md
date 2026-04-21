# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.4]

### Added

- `CustomAnswersStrategy`: new strategy that returns preconfigured answers for exact-match questions.

## [0.0.3]

### Added

- Hisotry api to read received requetss

## [0.0.2]

### Added

- Debug flag for detailled request output

### Changed

- When the last message is a tool call result, the result is returned as instead of the last user message

## [0.0.1]

### Added

- Configuration for port (default 8000).
- v1 endpoints for /v1/chat/completions, /v1/models and /v1/responses.

### Changed

- No default api-key -> no authorization needed by default.
- Override list configs with env vars now uses proper json syntax.
