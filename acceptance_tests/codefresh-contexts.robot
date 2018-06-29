*** Settings ***
Documentation     Tests to verify integration with attached Codefresh contexts
Library           Collections
Library           lib/CFStepHelm.py

*** Test Cases ***
CHART_REPO_URL is set automatically given CF_CTX_CF_HELM_DEFAULT_URL and normalized to contain a trailing slash
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Set to dictionary   ${env}  CF_CTX_CF_HELM_DEFAULT_URL   cm://h.cfcr.io/myaccount/default
    Run with env   ${env}
    Should have succeeded
    Output contains   cm://h.cfcr.io/myaccount/default/

Helm username and password added to an https CHART_REPO_URL given HELMREPO_USERNAME
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Set to dictionary   ${env}  CF_CTX_MYREPO_URL   https://myhelmrepo.com
    Set to dictionary   ${env}  HELMREPO_USERNAME   user
    Set to dictionary   ${env}  HELMREPO_PASSWORD   pass
    Run with env   ${env}
    Should have succeeded
    Output contains   https://user:pass@myhelmrepo.com
