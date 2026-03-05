---
name: piv
description: "PIV workflow orchestrator - Plan, Implement, Validate loop for systematic multi-phase software development. Use when building features phase-by-phase with PRPs, automated validation loops, or multi-agent orchestration."
user-invocable: true
disable-model-invocation: true
metadata:
  clawdbot:
    emoji: "🔄"
version: 1.1.0
---

# PIV - Plan Implement Validate

Systematic workflow orchestrator for methodical, phase-by-phase development.

## Core Concept

PIV implements a structured development loop:
1. **Plan**: Define requirements and approach
2. **Implement**: Execute the development work
3. **Validate**: Test and verify outcomes

## When to Use PIV

- Complex features requiring multiple phases
- Projects with clear validation criteria
- Multi-agent development workflows
- Quality-critical implementations
- Regulatory or compliance requirements

## Workflow Structure

### Plan Phase
- Requirements analysis
- Technical specification
- Risk assessment
- Resource planning
- Success criteria definition

### Implement Phase
- Code development
- Unit testing
- Documentation
- Progress tracking
- Integration preparation

### Validate Phase
- Functional testing
- Performance validation
- Security assessment
- User acceptance testing
- Compliance verification

## Usage

```bash
# Start a new PIV cycle
piv start "user authentication system"

# Plan phase
piv plan --requirements "OAuth 2.0, JWT tokens, password reset"

# Implement phase
piv implement --phase "backend" --agents 2

# Validate phase
piv validate --criteria "security, performance, usability"

# Complete cycle
piv complete --generate-report
```

## Configuration

```yaml
piv:
  default_phases: ["plan", "implement", "validate"]
  approval_gates: ["implement_to_validate", "validate_to_complete"]
  
validation:
  automated_tests: true
  security_scan: true
  performance_benchmarks: true
  code_review: required
  
agents:
  planner:
    models: ["gpt-4"]
    tools: ["analysis", "documentation"]
  
  implementer:
    models: ["codex"]
    tools: ["coding", "testing"]
  
  validator:
    models: ["gpt-4"]
    tools: ["testing", "security"]
```

## PRP System (Problem-Requirements-Plan)

PIV uses PRPs to structure each phase:

### Problem Definition
- Clear problem statement
- Success metrics
- Constraints and boundaries
- Stakeholder requirements

### Requirements Specification
- Functional requirements
- Non-functional requirements
- Technical constraints
- Business rules

### Plan Creation
- Technical approach
- Implementation strategy
- Risk mitigation
- Timeline and resources

## Validation Framework

### Automated Validation
- Unit test coverage (>90%)
- Integration tests
- Performance benchmarks
- Security scans

### Manual Validation
- Code review
- User acceptance testing
- Compliance verification
- Documentation review

### Quality Gates
- All tests passing
- Code review approved
- Security scan clean
- Performance benchmarks met

## Reporting

PIV generates comprehensive reports:
- Phase completion status
- Quality metrics
- Risk assessment
- Lessons learned
- Recommendations

## Integration

PIV integrates with:
- Version control systems
- CI/CD pipelines
- Project management tools
- Quality assurance systems
- Documentation platforms

## Best Practices

1. **Clear Success Criteria**: Define measurable outcomes
2. **Regular Checkpoints**: Monitor progress at each gate
3. **Comprehensive Testing**: Validate both functional and non-functional requirements
4. **Documentation**: Maintain detailed records throughout the process
5. **Continuous Improvement**: Learn from each cycle and refine the process

## Advanced Features

### Multi-Agent Orchestration
- Parallel execution where possible
- Agent specialization and coordination
- Conflict resolution and handoffs

### Adaptive Planning
- Dynamic plan adjustment based on findings
- Risk-based prioritization
- Resource optimization

### Compliance Mode
- Regulatory requirement tracking
- Audit trail maintenance
- Compliance reporting