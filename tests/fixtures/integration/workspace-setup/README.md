# Integration Test Fixture: Workspace Setup

This fixture provides a template flake for integration testing the complete west-nix workflow.

## Purpose

The integration test validates that:
1. westupdate can generate a lockfile from a west.yml manifest
2. The library functions (`mkWestProjects`, `mkWestWorkspace`) work correctly
3. The generated workspace is functional with West commands

## Usage

The test:
1. Generates a `westlock.nix` using westupdate
2. Copies this `flake.nix` template to a temporary directory
3. Replaces `WEST_NIX_PATH` with the actual path to the west-nix repository
4. Builds and runs the workspace setup
5. Verifies with `west list`

## Template Variables

- `WEST_NIX_PATH` - Replaced with the path to the west-nix repository root

## Files

- `flake.nix` - Template flake that demonstrates consuming west-nix library
