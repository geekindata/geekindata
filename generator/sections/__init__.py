from generator.sections import career, certifications, hero, showcase, telemetry, whoami


RENDERERS = {
    "hero": hero.render,
    "whoami": whoami.render,
    "telemetry": telemetry.render,
    "stack": showcase.render_stack,
    "projects": showcase.render_projects,
    "talks": showcase.render_talks,
    "career": career.render,
    "certifications": certifications.render,
}


def render_sections(data: dict) -> dict[str, str]:
    return {
        f"{name}-{theme}": renderer(data, theme)
        for name, renderer in RENDERERS.items()
        for theme in ("dark", "light")
    }
