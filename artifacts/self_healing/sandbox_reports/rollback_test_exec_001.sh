#!/bin/bash
# Auto-generated rollback script
# Candidate: test_exec_001

# Restore from git
git checkout HEAD -- 
git checkout HEAD -- .sandbox_test_file.txt

echo 'Rollback completed'