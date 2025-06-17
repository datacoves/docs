  - name: Create cluster-params.secret.yaml
    template:
      src: cluster-params.secret.j2
      dest: "../config/{{ hostname }}/cluster-params.secret.yml"
      backup: true


    hostname: "{{ lookup('env', 'DC_HOSTNAME') }}"
    release: "{{ lookup('env', 'DC_RELEASE') }}"
    sentry_dsn_operator: "{{ lookup('env', 'DC_SENTRY_DSN_OPERATOR') }}"
    sentry_dsn: "{{ lookup('env', 'DC_SENTRY_DSN') }}"
    slack_token: "{{ lookup('env', 'DC_SLACK_TOKEN') }}"


#
# export KUBECONFIG=/path/to/first/config:/path/to/second/config"