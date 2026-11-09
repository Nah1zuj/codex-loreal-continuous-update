# v5 policy overlay

Version 5 only stores rules that changed from version 4. Missing policy files
inherit their immutable v4 content through `PolicyRegistry`; the public runtime
version remains v5 and the manifest continues to include each effective rule's
content hash.
