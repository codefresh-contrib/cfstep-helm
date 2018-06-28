*** Settings ***
Documentation     Tests to verify functionality of ACTION=install
Library           Collections
Library           lib/CFStepHelm.py

*** Test Cases ***
Install local chart no overrides
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Run with env   ${env}
    Should have succeeded
    Output contains   helm upgrade

Install remote chart no overrides using CHART_REPO_URL
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Set to dictionary   ${env}  CHART_REPO_URL   https://myhelmrepo.com
    Run with env   ${env}
    Should have succeeded
    Output contains   helm upgrade
    Output contains   --repo https://myhelmrepo.com

Install chart with CHART_VERSION
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Set to dictionary   ${env}  CHART_VERSION   1.1.1
    Run with env   ${env}
    Should have succeeded
    Output contains   helm upgrade
    Output contains   --version 1.1.1

Install chart with NAMESPACE
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Set to dictionary   ${env}  NAMESPACE   staging
    Run with env   ${env}
    Should have succeeded
    Output contains   helm upgrade
    Output contains   --namespace=staging

Install detects CUSTOMFILE_ and VALUESFILE_ environment vars and converts correctly
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Set to dictionary   ${env}  CUSTOMFILE_FILE1    my/custom/file1.yaml
    Set to dictionary   ${env}  CUSTOMFILE_FILE2    my/custom/file2.yaml
    Set to dictionary   ${env}  VALUESFILE_FILE1    my/values/file1.yaml
    Set to dictionary   ${env}  VALUESFILE_FILE2    my/values/file2.yaml
    Run with env   ${env}
    Should have succeeded
    Output contains   helm upgrade
    Output contains   --values my/custom/file1.yaml
    Output contains   --values my/custom/file2.yaml
    Output contains   --values my/values/file1.yaml
    Output contains   --values my/values/file2.yaml

Install detects CUSTOM_ and VALUE_ environment vars and converts correctly
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Set to dictionary   ${env}  CUSTOM_myimage_pullPolicy   Always
    Set to dictionary   ${env}  VALUE_myimage_customField   Other
    Set to dictionary   ${env}  CUSTOM_env_open_STORAGE__AMAZON__BUCKET   my-s3-bucket
    Set to dictionary   ${env}  VALUE_env_open_STORAGE__AMAZON__REGION   us-west-2
    Run with env   ${env}
    Should have succeeded
    Output contains   helm upgrade
    Output contains   --set myimage.pullPolicy=Always
    Output contains   --set myimage.customField=Other
    Output contains   --set env.open.STORAGE_AMAZON_BUCKET=my-s3-bucket
    Output contains   --set env.open.STORAGE_AMAZON_REGION=us-west-2
