# Test Fixtures

Each subdirectory represents a test case with the following structure:

```
fixture-name/
├── in/
│   └── west.yml          # Input West manifest
└── out/
    └── westlock.nix      # Expected Nix output
```

## Adding New Test Cases

1. Create a new directory with a descriptive name
2. Create `in/west.yml` with the input manifest
3. Create `out/westlock.nix` with the expected output
4. Tests will automatically discover and run the new fixture

## Existing Test Cases

### zephyr-basic
Basic Zephyr project with HAL dependencies:
- 4 projects (zephyr, cmsis_6, hal_nordic, hal_stm32)
- Group filtering (-babblesim, -optional)
- Custom paths for HAL modules
