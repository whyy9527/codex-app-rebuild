---
name: aliyun-oauth-oss-session
description: |
  Fix private OSS deployment uploads when Aliyun ECS commands work with an OAuth
  profile but ossutil authentication fails, or an old default AK is disabled.
---

# Aliyun OAuth session in OSS transport

## Use when

An existing deployment uses `aliyun ecs` successfully through an OAuth profile,
but writes an ossutil credentials file containing only an access key pair.

## Failure mechanism

Aliyun CLI OAuth profiles can contain cached temporary `access_key_id`,
`access_key_secret`, and `sts_token` fields. ECS calls resolve the profile through
the CLI; an independently written ossutil config does not. Copying only the key
pair drops the session token and fails authentication. Switching to a disabled
long-lived default AK does not repair that missing token.

## Procedure

1. Preserve the deployment's exact authorized instance and domain. Perform its
   existing read-only instance validation using the chosen OAuth profile; this
   also lets the CLI refresh its cached session before the config is read.
2. Inspect field names or presence only. Do not print the credential values.
3. Reuse the deployment's temporary, mode-0600 ossutil config. Include
   `stsToken=<profile sts_token>` when that field is populated, alongside the
   existing `accessKeyID`, `accessKeySecret`, and regional endpoint. Keep the
   token absent for an ordinary AK profile.
4. Use the existing private-upload and signed-download flow. Remove the temporary
   config when finished and remove only the upload object owned by this run.

The implementation owner is
[deploy.py](../../../projects/valorant-predictor/scripts/deploy.py), function
`oss_credentials`; do not implement a second transport to work around this.

## Verification

From the repository root:

```sh
python3 -m unittest discover -s projects/valorant-predictor/tests -p 'test_deploy_credentials.py' -v
```

The fixture tests cover OAuth token propagation and unchanged ordinary AK
behavior. Real private OSS upload, checksum-verified server activation, public
asset checks and owned-upload cleanup have also been verified with this path.

## Avoid

- Do not expose keys, session tokens, signed URLs, or credential configs in logs,
  command arguments, Git, or public build output.
- Do not change the default profile, revive disabled keys, weaken TLS, or grant
  additional permissions as an authentication workaround.
- A successful upload is not proof of activation; keep the deployment's checksum,
  health, public-file and recovery checks.
