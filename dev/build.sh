#!/usr/bin/env bash
# twine register dist/pymlsql-1.1.3.tar.gz -r testpypi
twine upload --repository testpypi dist/* 

#twine register dist/pymlsql-1.1.3.tar.gz
#twine upload dist/*