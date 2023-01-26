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

Helm username and password added to an https CHART_REPO_URL given HELMREPO_USERNAME and HELMREPO_PASSWORD is encrypted
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
    Output contains   https://user:*****@myhelmrepo.com

Helm username and password added as parameters
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Set to dictionary   ${env}  CF_CTX_MYREPO_URL   https://myhelmrepo.com
    Set to dictionary   ${env}  HELMREPO_USERNAME   user
    Set to dictionary   ${env}  HELMREPO_PASSWORD   pass
    Set to dictionary   ${env}  CREDENTIALS_IN_ARGUMENTS   true
    Run with env   ${env}
    Should have succeeded
    Output contains   --username user --password pass

Azure context with az protocol gets converted to https and path added
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Set to dictionary   ${env}  CF_CTX_MYREPO_URL   az://my.azure.helm.repo.com
    Run with env   ${env}
    Should have succeeded
    Output contains   https://00000000-0000-0000-0000-000000000000:*****@my.azure.helm.repo.com/helm/v1/repo

Two repo should be added with right credentials for auth action with credentials in arguments
    &{env}=   Create dictionary
    Set to dictionary   ${env}  ACTION   auth
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  PRIMARY_HELM_CONTEXT   REPO1
    Set to dictionary   ${env}  CF_CTX_REPO1_URL   http://repo1.com
    Set to dictionary   ${env}  CF_CTX_REPO2_HELMREPO_PASSWORD   111
    Set to dictionary   ${env}  CF_CTX_REPO2_HELMREPO_USERNAME   aaa
    Set to dictionary   ${env}  CF_CTX_REPO2_URL   http://repo2.com
    Set to dictionary   ${env}  HELMREPO_PASSWORD   pass
    Set to dictionary   ${env}  HELMREPO_USERNAME   test
    Set to dictionary   ${env}  CREDENTIALS_IN_ARGUMENTS   true
    Set to dictionary   ${env}  DRY_RUN   true
    Run with env   ${env}
    Should have succeeded
    Output contains   helm repo add REPO1 http://repo1.com/ --username test --password pass
    Output contains   helm repo add REPO2 http://repo2.com/ --username aaa --password 111

Two repo should be added with right credentials for auth action
    &{env}=   Create dictionary
    Set to dictionary   ${env}  ACTION   auth
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  PRIMARY_HELM_CONTEXT   REPO1
    Set to dictionary   ${env}  CF_CTX_REPO1_URL   http://repo1.com
    Set to dictionary   ${env}  CF_CTX_REPO2_HELMREPO_PASSWORD   111
    Set to dictionary   ${env}  CF_CTX_REPO2_HELMREPO_USERNAME   aaa
    Set to dictionary   ${env}  CF_CTX_REPO2_URL   http://repo2.com
    Set to dictionary   ${env}  HELMREPO_PASSWORD   pass
    Set to dictionary   ${env}  HELMREPO_USERNAME   test
    Set to dictionary   ${env}  DRY_RUN   true
    Run with env   ${env}
    Should have succeeded
    Output contains   helm repo add REPO1 http://test:*****@repo1.com/
    Output contains   helm repo add REPO2 http://aaa:*****@repo2.com/


Should build right install command. With primary_helm_context argument and credentials in arguments
    &{env}=   Create dictionary
    Set to dictionary   ${env}  ACTION   install
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  CHART_NAME   tomcat
    Set to dictionary   ${env}  RELEASE_NAME   tomcat
    Set to dictionary   ${env}  CF_CTX_REPO1_URL   http://repo1.com
    Set to dictionary   ${env}  CF_CTX_REPO2_HELMREPO_PASSWORD   111
    Set to dictionary   ${env}  CF_CTX_REPO2_HELMREPO_USERNAME   aaa
    Set to dictionary   ${env}  CF_CTX_REPO2_URL   http://repo2.com
    Set to dictionary   ${env}  HELMREPO_PASSWORD   pass
    Set to dictionary   ${env}  HELMREPO_USERNAME   test
    Set to dictionary   ${env}  CREDENTIALS_IN_ARGUMENTS   true
    Set to dictionary   ${env}  PRIMARY_HELM_CONTEXT   REPO1
    Set to dictionary   ${env}  NAMESPACE   default
    Set to dictionary   ${env}  DRY_RUN   true
    Run with env   ${env}
    Should have succeeded
    Output contains   helm upgrade tomcat tomcat --install --reset-values --repo http://repo1.com/ --username test --password pass --namespace default

Should build right install command. Without primary_helm_context argument and credentials in arguments
    &{env}=   Create dictionary
    Set to dictionary   ${env}  ACTION   install
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  CHART_NAME   tomcat
    Set to dictionary   ${env}  RELEASE_NAME   tomcat
    Set to dictionary   ${env}  CF_CTX_REPO1_URL   http://repo1.com
    Set to dictionary   ${env}  CF_CTX_REPO2_HELMREPO_PASSWORD   111
    Set to dictionary   ${env}  CF_CTX_REPO2_HELMREPO_USERNAME   aaa
    Set to dictionary   ${env}  CF_CTX_REPO2_URL   http://repo2.com
    Set to dictionary   ${env}  HELMREPO_PASSWORD   pass
    Set to dictionary   ${env}  HELMREPO_USERNAME   test
    Set to dictionary   ${env}  CREDENTIALS_IN_ARGUMENTS   true
    Set to dictionary   ${env}  NAMESPACE   default
    Set to dictionary   ${env}  DRY_RUN   true
    Run with env   ${env}
    Should have succeeded
    Output contains   helm upgrade tomcat tomcat --install --reset-values --repo http://repo2.com/ --username aaa --password 111 --namespace default

Check register
    &{env}=   Create dictionary
    Set to dictionary   ${env}  ACTION   install
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  CHART_NAME   tomcat
    Set to dictionary   ${env}  RELEASE_NAME   tomcat
    Set to dictionary   ${env}  CF_CTX_REPO1_URL   http://repo1.com
    Set to dictionary   ${env}  CF_CTX_RE-PO_2_HELMREPO_PASSWORD   111
    Set to dictionary   ${env}  CF_CTX_RE-PO_2_HELMREPO_USERNAME   aaa
    Set to dictionary   ${env}  CF_CTX_RE-po_2_URL   http://repo2.com
    Set to dictionary   ${env}  HELMREPO_PASSWORD   pass
    Set to dictionary   ${env}  HELMREPO_USERNAME   test
    Set to dictionary   ${env}  CREDENTIALS_IN_ARGUMENTS   true
    Set to dictionary   ${env}  PRIMARY_HELM_CONTEXT   RE-po_2
    Set to dictionary   ${env}  NAMESPACE   default
    Set to dictionary   ${env}  DRY_RUN   true
    Run with env   ${env}
    Should have succeeded
    Output contains   helm upgrade tomcat tomcat --install --reset-values --repo http://repo2.com/ --username aaa --password 111 --namespace default
