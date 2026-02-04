## Makefile.src - Source folder configuration
# This file is included by the main Makefile

# Add SOURCE_FOLDER to deptry configuration if it exists
ifneq ($(wildcard $(SOURCE_FOLDER)),)
DEPTRY_FOLDERS += $(SOURCE_FOLDER)
endif
