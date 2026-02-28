def b(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    if not v.strip():  # GitHub Secrets missing => "" -> use default
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")
