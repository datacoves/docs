import jinja2


def escape_quotes(text: str):
    return text.replace('"', '\\"').replace("'", "\\'")


def render_template(template_content, context):
    environment = jinja2.Environment(
        # Throw if the template references an undefined variable.
        undefined=jinja2.StrictUndefined,
        lstrip_blocks=True,
        trim_blocks=True,
    )
    environment.filters["escape_quotes"] = escape_quotes
    template = environment.from_string(template_content)
    return template.render(context)


# Contexts


def build_user_context(user):
    """Builds user context"""
    return {
        "email": user.email,
        "name": user.name,
        "username": user.email_username,
        "slug": user.slug,
    }


def build_user_credential_context(user_credential):
    """Builds user credential context, with a subset of fields as we don't want to expose secrets"""

    conn_data = user_credential.combined_connection()
    public_key = _get_ssl_public_key(user_credential)
    return {
        "user": conn_data.get("user"),
        "account": conn_data.get("account"),
        "ssl_public_key": public_key,
    }


def build_user_credentials_context(user, env, creds: list = None):
    """creds, if provided, should be the user credentails already pre-loaded
    and properly filtered by 'env' in a list."""

    if creds is None:
        user_credentials = (
            user.credentials.select_related("connection_template__type")
            .select_related("ssl_key")
            .filter(environment=env, validated_at__isnull=False)
            .order_by("id")
        )

    else:
        user_credentials = [x for x in creds if x.validated_at is not None]
        user_credentials.sort(key=lambda x: x.id)

    connections = []
    for uc in user_credentials:
        conn_data = uc.combined_connection()
        conn_data["name"] = uc.name
        conn_data["slug"] = uc.slug
        conn_data["type"] = uc.connection_template.type_slug
        conn_data["ssl_public_key"] = _get_ssl_public_key(uc)
        connections.append(conn_data)
    return {"connections": connections, "environment": build_environment_context(env)}


def _get_ssl_public_key(user_credential):
    """Returns a user credential striped public key (without headers) if not none"""
    public_key = user_credential.ssl_key.public if user_credential.ssl_key else ""
    public_key = public_key.strip()
    if public_key.startswith("--"):  # strip -----BEGIN PUBLIC KEY-----, etc.
        public_key_lines = public_key.split("\n")
        public_key = "".join(public_key_lines[1:-1])
    return public_key


def build_environment_context(env):
    """Context with environment data useful for templating"""
    return {
        "dbt_home_path": env.dbt_home_path if env.dbt_home_path else "",
        "type": env.type,
        "slug": env.slug,
        "settings": env.settings,
        "release_profile": env.release_profile,
        "profile_flags": env.profile_flags,
        "dbt_profile": env.dbt_profile,
        "protected_branch": (
            env.project.release_branch if env.project.release_branch_protected else ""
        ),
    }
